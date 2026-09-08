import hashlib
import json
import uuid
from collections.abc import Mapping
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.marketplace import MarketplaceAccountFence, MarketplaceAccountReconciliation, MarketplaceAccountSession, MarketplaceAuditEvent, MarketplaceCommand, MarketplaceCommandStatus, MarketplaceCommandType, MarketplaceIdempotencyRecord, MarketplaceListingStatus, MarketplacePaymentAsset


class MarketplaceDomainError(ValueError):
    code = "MARKETPLACE_INVALID_OPERATION"


class InvalidStateTransition(MarketplaceDomainError):
    code = "MARKETPLACE_INVALID_STATE_TRANSITION"


class IdempotencyConflict(MarketplaceDomainError):
    code = "MARKETPLACE_IDEMPOTENCY_CONFLICT"


class AccountNotSafe(MarketplaceDomainError):
    code = "MARKETPLACE_ACCOUNT_NOT_SAFE"

    def __init__(self, reason_code: str):
        super().__init__(reason_code)
        self.reason_code = reason_code


ADVISORY_LOCK_SEED = 1296127045


def _require_postgresql(session: Session) -> None:
    if session.bind is None or session.bind.dialect.name != "postgresql":
        raise RuntimeError("Marketplace account fencing requires PostgreSQL")


def lock_account(session: Session, account_id: uuid.UUID) -> None:
    """Acquire the canonical cross-process transaction lock.

    C# uses this exact SQL and seed, avoiding any language-specific UUID hashing.
    """
    _require_postgresql(session)
    session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:account_id AS text), :seed))"), {"account_id": str(account_id), "seed": ADVISORY_LOCK_SEED})


def require_account_safe_for_mutation(session: Session, account_id: uuid.UUID) -> int:
    """Fail closed unless the account is offline and has no unresolved stale session."""
    lock_account(session, account_id)
    current = datetime.now(timezone.utc)
    active_session = session.get(MarketplaceAccountSession, account_id)
    if active_session is not None:
        if active_session.lease_expires_at <= current:
            reconciliation = session.get(MarketplaceAccountReconciliation, account_id)
            if reconciliation is None or reconciliation.required_fencing_token < active_session.fencing_token:
                session.merge(MarketplaceAccountReconciliation(
                    account_id=account_id,
                    required_fencing_token=active_session.fencing_token,
                    required_reason_code="MARKETPLACE_SESSION_EXPIRED_RECONCILIATION_REQUIRED",
                    required_at=current,
                ))
        raise AccountNotSafe("MARKETPLACE_SESSION_PRESENT")

    reconciliation = session.get(MarketplaceAccountReconciliation, account_id)
    if reconciliation is not None and (
        reconciliation.reconciled_fencing_token is None
        or reconciliation.reconciled_fencing_token < reconciliation.required_fencing_token
    ):
        raise AccountNotSafe("MARKETPLACE_RECONCILIATION_REQUIRED")

    return acquire_account_fence(session, account_id, "marketplace-worker", lock_already_held=True)


def defer_unsafe_command(session: Session, command: MarketplaceCommand, reason_code: str, *, retry_after: timedelta = timedelta(seconds=30)) -> None:
    """Persist a bounded retry without keeping a worker lease or busy-looping."""
    now = datetime.now(timezone.utc)
    command.status = MarketplaceCommandStatus.RETRYABLE_FAILED
    command.blocked_reason_code = reason_code
    command.last_error_code = reason_code
    command.available_at = now + retry_after
    command.failed_at = now
    command.worker_id = None
    command.worker_lease_expires_at = None
    session.add(MarketplaceAuditEvent(
        event_type="MARKETPLACE_COMMAND_BLOCKED_ACCOUNT_UNSAFE",
        correlation_id=command.correlation_id,
        account_id=command.account_id,
        command_id=command.id,
        metadata_json={"reason_code": reason_code, "retry_at": command.available_at.isoformat()},
    ))


def claim_next_command(session: Session, worker_id: str, *, lease: timedelta = timedelta(minutes=2)) -> MarketplaceCommand | None:
    """Claim one due command with SKIP LOCKED; abandoned leases are restart-safe."""
    _require_postgresql(session)
    now = datetime.now(timezone.utc)
    command = session.scalar(
        select(MarketplaceCommand)
        .where(
            MarketplaceCommand.available_at <= now,
            (MarketplaceCommand.status.in_([MarketplaceCommandStatus.PENDING, MarketplaceCommandStatus.RETRYABLE_FAILED]))
            | ((MarketplaceCommand.status == MarketplaceCommandStatus.PROCESSING) & (MarketplaceCommand.worker_lease_expires_at < now)),
        )
        .order_by(MarketplaceCommand.available_at, MarketplaceCommand.created_at)
        .with_for_update(skip_locked=True)
        .limit(1)
    )
    if command is None:
        return None
    command.status = MarketplaceCommandStatus.PROCESSING
    command.worker_id = worker_id
    command.worker_lease_expires_at = now + lease
    command.started_at = command.started_at or now
    command.attempts += 1
    command.blocked_reason_code = None
    return command


LISTING_TRANSITIONS = {
    MarketplaceListingStatus.PENDING_ESCROW: {MarketplaceListingStatus.ACTIVE, MarketplaceListingStatus.FAILED},
    MarketplaceListingStatus.ACTIVE: {MarketplaceListingStatus.PROCESSING, MarketplaceListingStatus.CANCEL_PENDING, MarketplaceListingStatus.EXPIRED},
    MarketplaceListingStatus.PROCESSING: {MarketplaceListingStatus.SOLD, MarketplaceListingStatus.ACTIVE, MarketplaceListingStatus.FAILED},
    MarketplaceListingStatus.CANCEL_PENDING: {MarketplaceListingStatus.CANCELLED, MarketplaceListingStatus.ACTIVE, MarketplaceListingStatus.FAILED},
    MarketplaceListingStatus.SOLD: set(),
    MarketplaceListingStatus.CANCELLED: set(),
    MarketplaceListingStatus.EXPIRED: set(),
    MarketplaceListingStatus.FAILED: set(),
}


def validate_listing_transition(current: MarketplaceListingStatus, target: MarketplaceListingStatus) -> None:
    if target not in LISTING_TRANSITIONS[current]:
        raise InvalidStateTransition(f"{current.value} -> {target.value}")


def validate_price_asset(asset: MarketplacePaymentAsset, amount: int) -> None:
    if not asset.enabled or not asset.can_be_listing_price:
        raise MarketplaceDomainError("MARKETPLACE_ASSET_NOT_AVAILABLE")
    if amount < asset.min_amount or (asset.max_amount is not None and amount > asset.max_amount):
        raise MarketplaceDomainError("MARKETPLACE_ASSET_AMOUNT_INVALID")


def canonical_payload_hash(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def create_idempotent_command(session: Session, *, account_id: uuid.UUID, operation: MarketplaceCommandType, idempotency_key: str, aggregate_type: str, aggregate_id: uuid.UUID, payload: Mapping[str, Any], correlation_id: uuid.UUID, character_id: uuid.UUID | None = None) -> tuple[MarketplaceCommand, bool]:
    request_hash = canonical_payload_hash(payload)
    existing = session.scalar(select(MarketplaceIdempotencyRecord).where(MarketplaceIdempotencyRecord.account_id == account_id, MarketplaceIdempotencyRecord.operation == operation.value, MarketplaceIdempotencyRecord.idempotency_key == idempotency_key))
    if existing is not None:
        if existing.request_hash != request_hash:
            raise IdempotencyConflict()
        command = session.get(MarketplaceCommand, existing.command_id)
        if command is None:
            raise MarketplaceDomainError("MARKETPLACE_IDEMPOTENCY_COMMAND_MISSING")
        return command, False

    command = MarketplaceCommand(command_type=operation, aggregate_type=aggregate_type, aggregate_id=aggregate_id, account_id=account_id, character_id=character_id, idempotency_key=idempotency_key, payload=dict(payload), payload_hash=request_hash, status=MarketplaceCommandStatus.PENDING, correlation_id=correlation_id)
    session.add(command)
    session.flush()
    session.add(MarketplaceIdempotencyRecord(account_id=account_id, operation=operation.value, idempotency_key=idempotency_key, request_hash=request_hash, command_id=command.id))
    session.flush()
    return command, True


def acquire_account_fence(session: Session, account_id: uuid.UUID, owner_id: str, *, lock_already_held: bool = False) -> int:
    """Acquire the transaction-scoped cross-process fence and return a monotonic token.

    Callers must keep the surrounding transaction open for the entire economic operation.
    Phase 3 must call the same PostgreSQL advisory lock from login and Offline Helper entry.
    """
    _require_postgresql(session)
    if not lock_already_held:
        lock_account(session, account_id)
    token = session.execute(text("""
        INSERT INTO marketplace_account_fences (account_id, fencing_token, last_owner_id, updated_at)
        VALUES (CAST(:account_id AS uuid), 1, :owner_id, now())
        ON CONFLICT (account_id) DO UPDATE
        SET fencing_token = marketplace_account_fences.fencing_token + 1,
            last_owner_id = EXCLUDED.last_owner_id,
            updated_at = now()
        RETURNING fencing_token
    """), {"account_id": str(account_id), "owner_id": owner_id}).scalar_one()
    return int(token)

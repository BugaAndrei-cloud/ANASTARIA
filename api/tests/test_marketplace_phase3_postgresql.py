import os
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import delete, text
from sqlalchemy.orm import Session

from app.database.engine import engine
from app.models.marketplace import (
    MarketplaceAccountFence,
    MarketplaceAccountReconciliation,
    MarketplaceAccountSession,
    MarketplaceCommand,
    MarketplaceCommandStatus,
    MarketplaceCommandType,
    MarketplaceSessionKind,
    MarketplaceSessionState,
)
from app.services.marketplace_domain import AccountNotSafe, claim_next_command, require_account_safe_for_mutation


pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="requires PostgreSQL")


@pytest.fixture
def account_id():
    value = uuid.uuid4()
    yield value
    with Session(engine) as session, session.begin():
        session.execute(delete(MarketplaceAccountSession).where(MarketplaceAccountSession.account_id == value))
        session.execute(delete(MarketplaceAccountReconciliation).where(MarketplaceAccountReconciliation.account_id == value))
        session.execute(delete(MarketplaceAccountFence).where(MarketplaceAccountFence.account_id == value))


def add_session(session: Session, account_id: uuid.UUID, state: MarketplaceSessionState, *, expired: bool = False, kind: MarketplaceSessionKind = MarketplaceSessionKind.ONLINE):
    now = datetime.now(timezone.utc)
    session.add(MarketplaceAccountSession(
        account_id=account_id,
        session_id=uuid.uuid4(),
        session_kind=kind,
        game_server_instance_id="pytest",
        fencing_token=1,
        state=state,
        heartbeat_at=now - (timedelta(minutes=5) if expired else timedelta()),
        lease_expires_at=now - timedelta(minutes=1) if expired else now + timedelta(minutes=2),
    ))


@pytest.mark.parametrize("state", list(MarketplaceSessionState))
@pytest.mark.parametrize("kind", list(MarketplaceSessionKind))
def test_every_persistent_session_state_and_kind_blocks(account_id, state, kind):
    with Session(engine) as session, session.begin():
        add_session(session, account_id, state, kind=kind)
    with Session(engine) as session, session.begin():
        with pytest.raises(AccountNotSafe, match="MARKETPLACE_SESSION_PRESENT"):
            require_account_safe_for_mutation(session, account_id)


def test_expired_lease_blocks_and_requires_reconciliation(account_id):
    with Session(engine) as session, session.begin():
        add_session(session, account_id, MarketplaceSessionState.ACTIVE, expired=True)
    with Session(engine) as session, session.begin():
        with pytest.raises(AccountNotSafe):
            require_account_safe_for_mutation(session, account_id)
        session.flush()
        reconciliation = session.get(MarketplaceAccountReconciliation, account_id)
        assert reconciliation is not None
        assert reconciliation.reconciled_at is None

    with Session(engine) as session, session.begin():
        session.execute(delete(MarketplaceAccountSession).where(MarketplaceAccountSession.account_id == account_id))
    with Session(engine) as session, session.begin():
        with pytest.raises(AccountNotSafe, match="MARKETPLACE_RECONCILIATION_REQUIRED"):
            require_account_safe_for_mutation(session, account_id)


def test_confirmed_logout_allows_retry_and_fence_is_monotonic(account_id):
    with Session(engine) as session, session.begin():
        first = require_account_safe_for_mutation(session, account_id)
    with Session(engine) as session, session.begin():
        second = require_account_safe_for_mutation(session, account_id)
    assert second == first + 1


def test_login_claim_waits_for_marketplace_transaction(account_id):
    market_locked = threading.Event()
    release_market = threading.Event()
    login_finished = threading.Event()

    def market():
        with Session(engine) as session, session.begin():
            require_account_safe_for_mutation(session, account_id)
            market_locked.set()
            assert release_market.wait(5)

    def login():
        assert market_locked.wait(5)
        with Session(engine) as session, session.begin():
            session.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(CAST(:id AS text), 1296127045))"), {"id": str(account_id)})
            login_finished.set()

    first = threading.Thread(target=market)
    second = threading.Thread(target=login)
    first.start(); second.start()
    assert market_locked.wait(5)
    assert not login_finished.wait(0.2)
    release_market.set()
    first.join(5); second.join(5)
    assert login_finished.is_set()


def test_two_workers_cannot_claim_same_command(account_id):
    command_id = uuid.uuid4()
    with Session(engine) as session, session.begin():
        session.add(MarketplaceCommand(
            id=command_id,
            command_type=MarketplaceCommandType.CREATE_LISTING,
            aggregate_type="listing",
            aggregate_id=uuid.uuid4(),
            account_id=account_id,
            idempotency_key=f"pytest-{uuid.uuid4()}",
            payload={}, payload_hash="0" * 64,
            status=MarketplaceCommandStatus.PENDING,
            correlation_id=uuid.uuid4(),
        ))
    try:
        first_session = Session(engine)
        first_session.begin()
        first = claim_next_command(first_session, "worker-a")
        with Session(engine) as second_session, second_session.begin():
            second = claim_next_command(second_session, "worker-b")
        assert first is not None and first.id == command_id
        assert second is None
        first_session.commit()
    finally:
        first_session.close()
        with Session(engine) as session, session.begin():
            session.execute(delete(MarketplaceCommand).where(MarketplaceCommand.id == command_id))

import pytest
from sqlalchemy.orm import Session

from app.database.engine import engine
from app.services.marketplace_invariants import scan_marketplace_invariants

pytestmark = pytest.mark.skipif(engine.dialect.name != "postgresql", reason="requires PostgreSQL")


def test_current_database_has_no_marketplace_physical_invariant_violations():
    with Session(engine) as session:
        results = scan_marketplace_invariants(session)
        assert len(results) == 20
        assert all(count == 0 for count in results.values()), results

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.dialects import postgresql

from app.modules.reservations.service import get_locked_reservation, serialize_reservation


class ScalarRecorder:
    def __init__(self, results):
        self.results = list(results)
        self.statements = []

    def scalar(self, statement):
        self.statements.append(statement)
        return self.results.pop(0)


def _postgres_sql(statement) -> str:
    return str(statement.compile(dialect=postgresql.dialect())).lower()


def test_get_locked_reservation_locks_only_reservation_row_before_loading_relationships() -> None:
    locked = SimpleNamespace(id=42)
    loaded = SimpleNamespace(id=42)
    db = ScalarRecorder([locked, loaded])

    reservation = get_locked_reservation(db, 42)

    assert reservation is loaded
    assert len(db.statements) == 2
    lock_sql = _postgres_sql(db.statements[0])
    load_sql = _postgres_sql(db.statements[1])
    assert " for update" in lock_sql
    assert " join " not in lock_sql
    assert "reservas" in lock_sql
    assert " for update" not in load_sql
    assert " join " in load_sql


def test_get_locked_reservation_preserves_not_found_error() -> None:
    db = ScalarRecorder([None])

    with pytest.raises(HTTPException) as exc_info:
        get_locked_reservation(db, 999)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail["code"] == "RESERVATION_NOT_FOUND"
    assert len(db.statements) == 1
    assert " for update" in _postgres_sql(db.statements[0])


def test_serialize_reservation_includes_complete_branch_data() -> None:
    reservation = SimpleNamespace(
        id=15,
        customer_id=4,
        customer=SimpleNamespace(first_name="Ana", last_name="Mora"),
        branch_id=2,
        branch=SimpleNamespace(
            name="Sucursal Centro",
            city=SimpleNamespace(name="Santa Cruz"),
            address="Av. Moda 123",
            phone="70000000",
            latitude=Decimal("-17.783333"),
            longitude=Decimal("-63.182125"),
        ),
        scheduled_for=None,
        status="PENDING",
        notes=None,
        expires_at=None,
        created_at=None,
        items=[],
    )

    payload = serialize_reservation(reservation)

    assert payload["branch_name"] == "Sucursal Centro"
    assert payload["branch_city_name"] == "Santa Cruz"
    assert payload["branch_address"] == "Av. Moda 123"
    assert payload["branch_phone"] == "70000000"
    assert payload["branch_latitude"] == -17.783333
    assert payload["branch_longitude"] == -63.182125

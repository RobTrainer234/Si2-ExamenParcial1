from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import CheckConstraint, Column, DateTime, Integer, MetaData, String, Table, create_engine, inspect, text
from sqlalchemy.exc import IntegrityError


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "s1o3m5q7u9w1_cu03_subscription_pause.py"
)


def load_migration():
    spec = spec_from_file_location("cu03_subscription_pause", MIGRATION_PATH)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_cu03_subscription_pause_upgrade_and_downgrade_round_trip():
    migration = load_migration()
    engine = create_engine("sqlite:///:memory:")
    metadata = MetaData()
    subscriptions = Table(
        "subscriptions",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("status", String(20), nullable=False),
        Column("started_at", DateTime, nullable=True),
        CheckConstraint(
            "status IN ('ACTIVE', 'CANCELLED', 'EXPIRED', 'SUSPENDED')",
            name="ck_subscriptions_status_valid",
        ),
    )

    with engine.connect() as connection:
        metadata.create_all(connection)
        connection.execute(subscriptions.insert().values(id=1, status="ACTIVE"))
        connection.commit()

        with Operations.context(MigrationContext.configure(connection)):
            migration.upgrade()

        connection.commit()
        upgraded = inspect(connection)
        assert "paused_at" in {column["name"] for column in upgraded.get_columns("subscriptions")}
        upgraded_constraint = next(
            constraint
            for constraint in upgraded.get_check_constraints("subscriptions")
            if constraint["name"] == "ck_subscriptions_status_valid"
        )
        assert "PAUSED" in upgraded_constraint["sqltext"]

        connection.execute(
            text("INSERT INTO subscriptions (id, status, paused_at) VALUES (:id, :status, :paused_at)"),
            {"id": 2, "status": "PAUSED", "paused_at": "2025-01-01 12:00:00"},
        )
        connection.commit()

        with Operations.context(MigrationContext.configure(connection)):
            migration.downgrade()

        connection.commit()
        downgraded = inspect(connection)
        assert "paused_at" not in {column["name"] for column in downgraded.get_columns("subscriptions")}
        assert connection.execute(text("SELECT status FROM subscriptions WHERE id = 2")).scalar_one() == "SUSPENDED"
        legacy_constraint = next(
            constraint
            for constraint in downgraded.get_check_constraints("subscriptions")
            if constraint["name"] == "ck_subscriptions_status_valid"
        )
        assert "PAUSED" not in legacy_constraint["sqltext"]

        with pytest.raises(IntegrityError):
            connection.execute(text("INSERT INTO subscriptions (id, status) VALUES (3, 'PAUSED')"))
        connection.rollback()

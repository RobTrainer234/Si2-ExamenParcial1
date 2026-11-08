import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "w5s7u9x1z3b5_paid_signup_email_outbox.py"
)


def load_migration():
    spec = spec_from_file_location("paid_signup_email_outbox", MIGRATION_PATH)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def _assert_round_trip(connection, migration):
    connection.execute(text("CREATE TABLE pending_paid_signups (id INTEGER PRIMARY KEY)"))
    connection.commit()

    with Operations.context(MigrationContext.configure(connection)):
        migration.upgrade()
    connection.commit()

    upgraded = inspect(connection)
    assert {"email_verification_challenges", "email_outbox", "pending_paid_signups"}.issubset(
        set(upgraded.get_table_names())
    )
    pending_columns = {column["name"] for column in upgraded.get_columns("pending_paid_signups")}
    assert {"checkout_capability_hash", "capability_expires_at"}.issubset(pending_columns)

    with Operations.context(MigrationContext.configure(connection)):
        migration.downgrade()
    connection.commit()

    downgraded = inspect(connection)
    assert "email_verification_challenges" not in downgraded.get_table_names()
    assert "email_outbox" not in downgraded.get_table_names()
    assert {
        column["name"] for column in downgraded.get_columns("pending_paid_signups")
    } == {"id"}


def test_paid_signup_email_migration_upgrade_and_downgrade_round_trip_sqlite():
    migration = load_migration()
    engine = create_engine("sqlite:///:memory:")
    try:
        with engine.connect() as connection:
            _assert_round_trip(connection, migration)
    finally:
        engine.dispose()


def test_paid_signup_email_migration_upgrade_and_downgrade_round_trip_postgresql():
    database_url = os.environ.get("MIGRATION_TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("MIGRATION_TEST_DATABASE_URL is not set")

    migration = load_migration()
    schema = f"migration_test_{uuid4().hex}"
    quoted_schema = f'"{schema}"'
    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            connection.execute(text(f"CREATE SCHEMA {quoted_schema}"))
            connection.execute(text(f"SET search_path TO {quoted_schema}"))
            connection.commit()
            _assert_round_trip(connection, migration)
    finally:
        try:
            with engine.begin() as cleanup:
                cleanup.execute(text(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE"))
        finally:
            engine.dispose()

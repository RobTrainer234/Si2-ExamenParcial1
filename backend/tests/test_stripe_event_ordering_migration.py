import os
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from uuid import uuid4
from unittest.mock import Mock, call, patch

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text


MIGRATION_PATH = (
    Path(__file__).parents[1]
    / "migrations"
    / "versions"
    / "v4r6t8z0b2d4_stripe_event_ordering.py"
)


def load_migration():
    spec = spec_from_file_location("stripe_event_ordering", MIGRATION_PATH)
    assert spec and spec.loader
    migration = module_from_spec(spec)
    spec.loader.exec_module(migration)
    return migration


def test_sequence_helper_contains_postgresql_sync_sql():
    migration = load_migration()
    connection = Mock()
    connection.dialect.name = "postgresql"
    execute = Mock()

    with patch.object(migration.op, "get_bind", return_value=connection), patch.object(
        migration.op, "execute", execute
    ):
        migration._synchronize_subscription_id_sequence()

    sql = str(execute.call_args.args[0])
    assert "pg_get_serial_sequence('subscriptions', 'id')" in sql
    assert "MAX(id)" in sql
    assert "setval" in sql
    assert "false" in sql.lower()
    assert "true" in sql.lower()


def test_upgrade_and_downgrade_invoke_sequence_helper():
    migration = load_migration()
    batch_context = Mock()
    batch_context.__enter__ = Mock(return_value=Mock())
    batch_context.__exit__ = Mock(return_value=False)

    with patch.object(migration.op, "batch_alter_table", return_value=batch_context), patch.object(
        migration, "_synchronize_subscription_id_sequence"
    ) as synchronize:
        migration.upgrade()
        migration.downgrade()

    assert synchronize.call_args_list == [call(), call()]


@pytest.mark.parametrize("subscription_ids", [[], [2, 5, 11]])
def test_postgresql_upgrade_and_downgrade_preserve_serial_sequence(subscription_ids):
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
            connection.execute(text("CREATE TABLE subscriptions (id SERIAL PRIMARY KEY)"))
            for subscription_id in subscription_ids:
                connection.execute(
                    text("INSERT INTO subscriptions (id) VALUES (:subscription_id)"),
                    {"subscription_id": subscription_id},
                )
            connection.commit()

            expected_next_id = max(subscription_ids, default=0) + 1
            with Operations.context(MigrationContext.configure(connection)):
                migration.upgrade()
            connection.commit()
            assert "provider_event_created_at" in {
                column["name"] for column in inspect(connection).get_columns("subscriptions")
            }
            assert connection.execute(
                text("SELECT nextval(pg_get_serial_sequence('subscriptions', 'id'))")
            ).scalar_one() == expected_next_id

            with Operations.context(MigrationContext.configure(connection)):
                migration.downgrade()
            connection.commit()
            assert "provider_event_created_at" not in {
                column["name"] for column in inspect(connection).get_columns("subscriptions")
            }
            assert connection.execute(
                text("SELECT nextval(pg_get_serial_sequence('subscriptions', 'id'))")
            ).scalar_one() == expected_next_id
    finally:
        try:
            with engine.begin() as cleanup:
                cleanup.execute(text(f"DROP SCHEMA IF EXISTS {quoted_schema} CASCADE"))
        finally:
            engine.dispose()

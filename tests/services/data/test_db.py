import sqlite3

import pytest

from app.services.data.db import (
  MIGRATIONS_DIR,
  apply_pending_migrations,
  current_schema_version,
  db_connection,
  db_transaction,
)

BASELINE_MIGRATION = MIGRATIONS_DIR / "v0.1.0.sql"


def _open(db_path):
  connection = sqlite3.connect(db_path)
  connection.execute("PRAGMA foreign_keys = ON")
  return connection


def _create_legacy_db(db_path):
  connection = _open(db_path)

  try:
    connection.executescript(BASELINE_MIGRATION.read_text())
    connection.commit()
  finally:
    connection.close()


def test_init_db_stamps_schema_version(gen_init_db):
  connection = _open(gen_init_db)

  try:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
  finally:
    connection.close()

  assert version == current_schema_version()


def test_apply_pending_migrations_migrates_legacy_db(tmp_path):
  db_path = tmp_path / "legacy.db"
  _create_legacy_db(db_path)

  connection = _open(db_path)

  try:
    connection.execute(
      """
      INSERT INTO custom_fields (name, field_type)
      VALUES ('Serial', 'text')
      """
    )
    connection.commit()
  finally:
    connection.close()

  apply_pending_migrations(db_path=db_path)

  connection = _open(db_path)

  try:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    columns = {
      row[1]: row for row in connection.execute("PRAGMA table_info(custom_fields)")
    }
    field = connection.execute(
      "SELECT value FROM inventory_item_fields LIMIT 1"
    ).fetchone()

    connection.execute(
      """
      INSERT INTO custom_fields (name, field_type)
      VALUES ('Expires', 'expiry_date')
      """
    )
    connection.commit()

    copyable_default = columns["copyable"][4]
    field_id = connection.execute(
      "SELECT id FROM custom_fields WHERE name = 'Serial'"
    ).fetchone()[0]
  finally:
    connection.close()

  assert version == current_schema_version()
  assert int(copyable_default) == 0
  assert field_id is not None
  assert field is None


def test_apply_pending_migrations_noop_when_current(gen_init_db):
  apply_pending_migrations(db_path=gen_init_db)

  connection = _open(gen_init_db)

  try:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
  finally:
    connection.close()

  assert version == current_schema_version()


def test_db_transaction_rejects_db_path_when_nested(gen_test_data_admin):
  with db_connection(), pytest.raises(ValueError), db_transaction(db_path="other.db"):
    pass


def test_db_connection_rejects_db_path_when_nested(gen_test_data_admin):
  with db_transaction(), pytest.raises(ValueError), db_connection(db_path="other.db"):
    pass


def test_db_connection_enables_wal_mode(gen_test_data_admin):
  with db_connection() as connection:
    mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode == "wal"


def test_db_connection_sets_busy_timeout(gen_test_data_admin):
  with db_connection() as connection:
    timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert timeout == 5000

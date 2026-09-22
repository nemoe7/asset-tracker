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

    with pytest.raises(sqlite3.IntegrityError):
      connection.execute(
        "INSERT INTO custom_fields (name, field_type) VALUES ('serial', 'text')"
      )
  finally:
    connection.close()

  assert version == current_schema_version()
  assert int(copyable_default) == 0
  assert field_id is not None
  assert field is None


def _insert_legacy_item_and_values(db_path, field_ids):
  connection = _open(db_path)

  try:
    connection.execute(
      """
      INSERT INTO inventory_items (
        id, name, created_at, updated_at
      )
      VALUES ('item-1', 'Test item', datetime('now'), datetime('now'))
      """
    )

    for field_id, value in zip(field_ids, ("one", "two", "three")):
      connection.execute(
        """
        INSERT INTO inventory_item_fields (item_id, field_id, value)
        VALUES ('item-1', ?, ?)
        """,
        (field_id, value),
      )

    connection.commit()
  finally:
    connection.close()


def test_apply_pending_migrations_preserves_values_and_repairs_collisions(tmp_path):
  db_path = tmp_path / "legacy.db"
  _create_legacy_db(db_path)
  connection = _open(db_path)

  try:
    connection.execute(
      """
      INSERT INTO users (
        username, name, password_hash, created_at, updated_at
      )
      VALUES ('migration-user', 'Migration User', 'hash', datetime('now'), datetime('now'))
      """
    )

    field_ids = []
    for name in ("Serial", "serial", "serial (2)"):
      field_ids.append(
        connection.execute(
          "INSERT INTO custom_fields (name, field_type) VALUES (?, 'text')",
          (name,),
        ).lastrowid
      )

    connection.commit()
  finally:
    connection.close()

  _insert_legacy_item_and_values(db_path, field_ids)
  apply_pending_migrations(db_path=db_path)

  connection = _open(db_path)

  try:
    fields = connection.execute(
      "SELECT id, name FROM custom_fields ORDER BY id"
    ).fetchall()
    values = connection.execute(
      """
      SELECT field_id, value
      FROM inventory_item_fields
      WHERE item_id = 'item-1'
      ORDER BY field_id
      """
    ).fetchall()
    audit_details = connection.execute(
      """
      SELECT entity_id, details
      FROM audit_log
      WHERE action = 'renamed' AND entity_type = 'custom_field'
      ORDER BY id
      """
    ).fetchall()
  finally:
    connection.close()

  assert [row[0] for row in fields] == field_ids
  assert [row[1] for row in fields] == ["Serial", "serial (2)", "serial (2) (2)"]
  assert [row[1] for row in values] == ["one", "two", "three"]
  assert len(audit_details) == 2
  assert '"old_name":"serial"' in audit_details[0][1]
  assert '"new_name":"serial (2)"' in audit_details[0][1]


def test_apply_pending_migrations_rolls_back_failed_migration(tmp_path, monkeypatch):
  db_path = tmp_path / "legacy.db"
  migration_dir = tmp_path / "migrations"
  migration_dir.mkdir()
  _create_legacy_db(db_path)
  connection = _open(db_path)

  try:
    field_id = connection.execute(
      "INSERT INTO custom_fields (name, field_type) VALUES ('Serial', 'text')"
    ).lastrowid
    connection.execute(
      """
      INSERT INTO inventory_items (id, name, created_at, updated_at)
      VALUES ('item-1', 'Test item', datetime('now'), datetime('now'))
      """
    )
    connection.execute(
      """
      INSERT INTO inventory_item_fields (item_id, field_id, value)
      VALUES ('item-1', ?, 'original')
      """,
      (field_id,),
    )
    connection.commit()
  finally:
    connection.close()

  migration_text = (
    MIGRATIONS_DIR / "v0.1.3.sql"
  ).read_text() + "\nSELECT migration_failure();\n"
  (migration_dir / "v0.1.3.sql").write_text(migration_text)
  monkeypatch.setattr("app.services.data.db.MIGRATIONS_DIR", migration_dir)

  with pytest.raises(sqlite3.OperationalError):
    apply_pending_migrations(db_path=db_path)

  connection = _open(db_path)

  try:
    version = connection.execute("PRAGMA user_version").fetchone()[0]
    field = connection.execute("SELECT id, name FROM custom_fields").fetchone()
    value = connection.execute("SELECT value FROM inventory_item_fields").fetchone()
    rebuilt_table = connection.execute(
      """
      SELECT 1
      FROM sqlite_master
      WHERE type = 'table' AND name = 'custom_fields_new'
      """
    ).fetchone()
  finally:
    connection.close()

  assert version == 0
  assert (field[0], field[1]) == (field_id, "Serial")
  assert value[0] == "original"
  assert rebuilt_table is None


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


def test_migration_statements_split():
  """Regression test: _migration_statements should split on semicolons."""
  from app.services.data.db import _migration_statements

  script = """
  CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
  INSERT INTO users VALUES (1, 'Alice');
  CREATE INDEX idx_users_name ON users(name);
  """

  statements = list(_migration_statements(script))
  assert len(statements) == 3
  assert statements[0].strip() == "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"
  assert statements[1].strip() == "INSERT INTO users VALUES (1, 'Alice')"
  assert statements[2].strip() == "CREATE INDEX idx_users_name ON users(name)"

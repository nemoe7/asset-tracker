import sqlite3

import pytest

from app.services.data.backups import create_backup
from app.services.data.audit import get_audit_logs
from app.services.exceptions.data.backups import BackupError


def open_backup(data):
  connection = sqlite3.connect(":memory:")

  connection.deserialize(data)

  return connection


def test_create_backup_returns_db_bytes_without_storing_any_file(
  gen_test_data_admin,
):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.inventory import create_item

  token = set_current_user(gen_test_data_admin)

  try:
    create_item("Alpha Asset")
  finally:
    reset_current_user(token)

  result = create_backup(gen_test_data_admin)

  data = result["data"]

  assert isinstance(data, bytes)
  assert data.startswith(b"SQLite format 3\x00")
  assert result["filename"].startswith("backup-")
  assert result["filename"].endswith(".db")
  assert isinstance(result["completed_at"], str)

  connection = open_backup(data)

  history = connection.execute(
    "SELECT COUNT(*) FROM backup_history WHERE path IS NULL"
  ).fetchone()

  tables = connection.execute(
    "SELECT COUNT(*) FROM inventory_items"
  ).fetchone()

  connection.close()

  # The backup itself contains the data and history rows recorded at the
  # time of the copy; nothing is stored on the server (path stays NULL).
  assert tables[0] == 1


def test_create_backup_bytes_contain_backed_up_audit_log(gen_test_data_admin):
  result = create_backup(gen_test_data_admin)

  connection = open_backup(result["data"])

  rows = connection.execute(
    "SELECT details FROM audit_log WHERE action = 'backed_up'"
  ).fetchall()

  connection.close()

  assert len(rows) == 1
  assert result["filename"] in rows[0][0]


def test_create_backup_records_history_after_success(gen_test_data_admin):
  create_backup(gen_test_data_admin)

  from app.services.data.db import db_connection

  with db_connection() as connection:
    rows = connection.execute(
      """
      SELECT user_id, scheduled_at, completed_at, path
      FROM backup_history
      """
    ).fetchall()

  assert len(rows) == 1
  assert rows[0]["user_id"] == gen_test_data_admin
  assert rows[0]["scheduled_at"] is None
  assert rows[0]["path"] is None
  assert rows[0]["completed_at"]


def test_create_backup_failure_writes_no_history(gen_test_data_admin, monkeypatch):
  import app.services.data.backups as backups

  def failing_copy():
    raise BackupError()

  monkeypatch.setattr(backups, "_backup_bytes", failing_copy)

  with pytest.raises(BackupError):
    create_backup(gen_test_data_admin)

  from app.services.data.db import db_connection

  with db_connection() as connection:
    rows = connection.execute(
      "SELECT COUNT(*) FROM backup_history"
    ).fetchone()

  assert rows[0] == 0

import io
import json
import sqlite3

import pytest

from app.services.data.backups import create_backup
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


# ==================== restore_backup ====================


def make_upload(data):
  from werkzeug.datastructures import FileStorage

  return FileStorage(
    stream=io.BytesIO(data),
    filename="backup-20260904-000000.db",
  )


def test_restore_backup_round_trip_restores_all_data(gen_test_data_admin):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.backups import restore_backup
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field
  from app.services.data.inventory import (
    create_item,
    get_item,
  )
  from app.services.data.locations import create_location, get_location
  from app.services.data.users import get_user_by_username

  token = set_current_user(gen_test_data_admin)

  try:
    location_id = create_location("Office")
    serial_id = create_custom_field("Serial", "text")
    alpha_id = create_item("Alpha Asset", location_id=location_id)
    set_custom_field_value(alpha_id, serial_id, "SN-1")

    result = create_backup(gen_test_data_admin)

    # Mutate the live database after the backup was taken.
    beta_id = create_item("Beta Asset")
  finally:
    reset_current_user(token)

  restore_backup(make_upload(result["data"]))

  alpha = get_item(alpha_id)

  assert alpha["name"] == "Alpha Asset"
  assert alpha["location_name"] == "Office"
  assert alpha["custom_fields"]["Serial"] == "SN-1"

  assert get_item(beta_id) is None
  assert get_location(location_id) is not None
  assert get_user_by_username("test_admin") is not None


def test_restore_records_restored_audit_log_identifying_backup(
  gen_test_data_admin,
):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.backups import restore_backup
  from app.services.data.inventory import create_item

  token = set_current_user(gen_test_data_admin)

  try:
    create_item("Alpha Asset")

    result = create_backup(gen_test_data_admin)
  finally:
    reset_current_user(token)

  restore_backup(make_upload(result["data"]))

  from app.services.data.db import db_connection

  with db_connection() as connection:
    rows = connection.execute(
      """
      SELECT details
      FROM audit_log
      WHERE action = 'restored'
      ORDER BY id DESC
      LIMIT 1
      """
    ).fetchall()

  assert len(rows) == 1

  details = json.loads(rows[0]["details"])

  assert details["backup_filename"] == result["filename"]
  assert details["backup_completed_at"]


def test_restore_backup_without_backed_up_entry_records_unknown(
  gen_test_data_admin,
):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.backups import restore_backup

  token = set_current_user(gen_test_data_admin)

  try:
    result = create_backup(gen_test_data_admin)
  finally:
    reset_current_user(token)

  connection = open_backup(result["data"])

  connection.execute("DELETE FROM audit_log WHERE action = 'backed_up'")

  connection.commit()

  stripped = connection.serialize()

  connection.close()

  restore_backup(make_upload(stripped))

  from app.services.data.db import db_connection

  with db_connection() as connection:
    rows = connection.execute(
      "SELECT details FROM audit_log WHERE action = 'restored'"
    ).fetchall()

  assert len(rows) == 1
  assert json.loads(rows[0]["details"])["backup_filename"] == "unknown"
  assert json.loads(rows[0]["details"])["backup_completed_at"] == "unknown"


def test_restore_invalid_file_raises_invalid_backup(gen_test_data_admin):
  from app.services.data.backups import restore_backup
  from app.services.exceptions.data.backups import InvalidBackupError

  with pytest.raises(InvalidBackupError):
    restore_backup(make_upload(b"this is not a sqlite database at all"))


def test_restore_invalid_file_leaves_live_db_untouched(gen_test_data_admin):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.backups import restore_backup
  from app.services.data.inventory import create_item, get_items

  token = set_current_user(gen_test_data_admin)

  try:
    create_item("Alpha Asset")
  finally:
    reset_current_user(token)

  with pytest.raises(Exception):
    restore_backup(make_upload(b"garbage"))

  assert [item["name"] for item in get_items()] == ["Alpha Asset"]

  from app.services.data.audit import get_audit_logs

  assert not any(
    log["action"] == "restored" for log in get_audit_logs()
  )

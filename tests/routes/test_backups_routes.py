import io

import pytest


def make_backup_upload(data):
  return {"file": (io.BytesIO(data), "backup-20260904-000000.db")}


def multipart(data):
  return {**data, "content_type": "multipart/form-data"}


# ==================== POST /backups/create ====================


def test_create_backup_requires_backups_create_permission(
  gen_test_client,
  gen_test_admin,
):
  from app.services.exceptions.auth.authorization import PermissionDeniedError
  from werkzeug.security import generate_password_hash

  import sqlite3

  import config

  connection = sqlite3.connect(config.DB_PATH)

  connection.execute(
    """
    INSERT INTO users (
      username,
      name,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    """,
    ("restricted_user", "Restricted", generate_password_hash("restricted1")),
  )

  connection.commit()
  connection.close()

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "restricted_user",
      "password": "restricted1",
    },
  )

  with pytest.raises(PermissionDeniedError):
    gen_test_client.post("/backups/create")


def test_create_backup_returns_backup_file_download_to_requester(
  gen_test_admin_client,
  gen_test_item,
):
  import sqlite3

  gen_test_item(name="Alpha Asset")

  response = gen_test_admin_client.post("/backups/create")

  assert response.status_code == 200
  assert response.mimetype == "application/x-sqlite3"
  assert "attachment" in response.headers["Content-Disposition"]
  assert "backup-" in response.headers["Content-Disposition"]

  data = response.get_data()

  assert data.startswith(b"SQLite format 3\x00")

  connection = sqlite3.connect(":memory:")

  connection.deserialize(data)

  items = connection.execute(
    "SELECT COUNT(*) FROM inventory_items"
  ).fetchone()

  connection.close()

  assert items[0] == 1


def test_create_backup_failure_returns_500_without_success(
  gen_test_admin_client,
  monkeypatch,
):
  import app.services.data.backups as backups

  from app.services.exceptions.data.backups import BackupError

  def failing_copy():
    raise BackupError()

  monkeypatch.setattr(backups, "_backup_bytes", failing_copy)

  response = gen_test_admin_client.post("/backups/create")

  assert response.status_code == 500
  assert b"SQLite format 3" not in response.get_data()

  from app.services.data.db import db_connection

  with db_connection() as connection:
    rows = connection.execute(
      "SELECT COUNT(*) FROM backup_history"
    ).fetchone()

  assert rows[0] == 0

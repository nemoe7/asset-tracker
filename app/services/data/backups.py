import json
import sqlite3
from datetime import datetime

import config

from ..auth.context import get_current_user
from .audit import create_audit_log
from .db import db_connection, db_transaction
from ..exceptions.data.backups import BackupError, InvalidBackupError

_CORE_TABLES = ("users", "inventory_items", "custom_fields", "audit_log")


def _backup_bytes():
  with db_connection() as source:
    target = sqlite3.connect(":memory:")

    try:
      source.backup(target)
      return target.serialize()
    finally:
      target.close()


def create_backup(user_id):
  filename = f"backup-{datetime.now():%Y%m%d-%H%M%S}.db"

  # Recorded first so the backup file contains the audit entry of its own
  # creation. If the copy fails, the live DB keeps this entry but the
  # backup_history row correctly stays absent (REL-005).
  create_audit_log(
    action="backed_up",
    entity_type="inventory",
    entity_id="backup",
    details={"filename": filename},
  )

  try:
    data = _backup_bytes()
  except sqlite3.Error as error:
    raise BackupError() from error

  completed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

  # Nothing is stored with the app: history records who requested the
  # backup and when; path stays NULL (scheduled backups are out of scope).
  with db_transaction() as connection:
    connection.execute(
      """
      INSERT INTO backup_history (user_id, scheduled_at, completed_at, path)
      VALUES (?, NULL, ?, NULL)
      """,
      (user_id, completed_at),
    )

  return {
    "filename": filename,
    "data": data,
    "completed_at": completed_at,
  }


def _validated_backup_connection(data):
  source = sqlite3.connect(":memory:")

  source.row_factory = sqlite3.Row

  try:
    try:
      source.deserialize(data)

      for table in _CORE_TABLES:
        row = source.execute(
          """
          SELECT 1
          FROM sqlite_master
          WHERE type = 'table'
            AND name = ?
          """,
          (table,),
        ).fetchone()

        if row is None:
          raise InvalidBackupError()
    except sqlite3.Error as error:
      raise InvalidBackupError() from error
  except Exception:
    source.close()
    raise

  return source


def _backed_up_identity(source):
  row = source.execute(
    """
    SELECT user_id, details, timestamp
    FROM audit_log
    WHERE action = 'backed_up'
    ORDER BY id DESC
    LIMIT 1
    """
  ).fetchone()

  if row is None:
    return {
      "user_id": None,
      "filename": "unknown",
      "completed_at": "unknown",
    }

  try:
    details = json.loads(row["details"]) if row["details"] else {}
  except json.JSONDecodeError:
    details = {}

  return {
    "user_id": row["user_id"],
    "filename": details.get("filename") or "unknown",
    "completed_at": row["timestamp"] or "unknown",
  }


def _resolve_restored_audit_user_id(connection, preferred_ids):
  for user_id in preferred_ids:
    if user_id is None:
      continue

    row = connection.execute(
      "SELECT 1 FROM users WHERE id = ?",
      (user_id,),
    ).fetchone()

    if row is not None:
      return user_id

  row = connection.execute(
    "SELECT id FROM users ORDER BY id LIMIT 1"
  ).fetchone()

  return row["id"] if row is not None else None


def restore_backup(file_storage, db_path=None):
  db_path = db_path or config.DB_PATH

  data = file_storage.read()

  source = _validated_backup_connection(data)

  try:
    identity = _backed_up_identity(source)

    # Validation is complete before the live database is touched.
    destination = sqlite3.connect(db_path)

    try:
      source.backup(destination)
      destination.commit()
    finally:
      destination.close()
  finally:
    source.close()

  with db_transaction() as connection:
    user_id = _resolve_restored_audit_user_id(
      connection,
      [get_current_user(), identity["user_id"]],
    )

    if user_id is not None:
      connection.execute(
        """
        INSERT INTO audit_log (
          user_id,
          action,
          entity_type,
          entity_id,
          details,
          timestamp
        )
        VALUES (?, 'restored', 'inventory', 'backup', ?, datetime('now'))
        """,
        (
          user_id,
          json.dumps(
            {
              "backup_filename": identity["filename"],
              "backup_completed_at": identity["completed_at"],
            },
          ),
        ),
      )

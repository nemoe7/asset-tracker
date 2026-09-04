import sqlite3
from datetime import datetime

import config

from .audit import create_audit_log
from .db import db_connection, db_transaction
from ..exceptions.data.backups import BackupError

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

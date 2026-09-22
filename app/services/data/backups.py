import json
import sqlite3
from datetime import datetime, timezone

import config

from ..auth.context import get_current_user
from ..exceptions.data.backups import BackupError, InvalidBackupError
from ..exceptions.data.common import InvalidInputError
from .audit import create_audit_log
from .db import db_connection, db_transaction

_CORE_TABLES = (
  "users",
  "roles",
  "permissions",
  "locations",
  "inventory_items",
  "custom_fields",
  "user_roles",
  "role_permissions",
  "user_permissions",
  "inventory_item_fields",
  "audit_log",
  "export_templates",
  "backup_config",
  "backup_history",
)


def _backup_bytes():
  with db_connection() as source:
    target = sqlite3.connect(":memory:")

    try:
      source.backup(target)
      target.execute("VACUUM")
      return target.serialize()
    finally:
      target.close()


def create_backup(user_id):
  filename = f"backup-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.db"

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

  completed_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

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
          raise InvalidInputError("backup missing tables")
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

  row = connection.execute("SELECT id FROM users ORDER BY id LIMIT 1").fetchone()

  return row["id"] if row is not None else None


def restore_backup(file_storage, db_path=None):
  db_path = db_path or config.DB_PATH
  db_path.parent.mkdir(parents=True, exist_ok=True)

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


# --- backup config (scheduled backups) ---

_DEFAULT_SCHEDULE = {"type": "weekly", "day": 6, "time": "03:00"}
_RECURRENCE_TYPES = ("daily", "weekly", "bi-weekly", "monthly")
_TIME_LENGTH = 5


def _validate_schedule(schedule):
  if not isinstance(schedule, dict):
    raise InvalidInputError("schedule must be an object")
  schedule_type = schedule.get("type")
  if schedule_type not in _RECURRENCE_TYPES:
    raise InvalidInputError("invalid recurrence type")
  time_value = schedule.get("time")
  if (
    not isinstance(time_value, str)
    or len(time_value) != _TIME_LENGTH
    or time_value[2] != ":"
  ):
    raise InvalidInputError("time must be HH:MM (24h)")
  hours, minutes = time_value.split(":")
  if not (hours.isdigit() and minutes.isdigit()):
    raise InvalidInputError("time must be HH:MM (24h)")
  if not (0 <= int(hours) <= 23 and 0 <= int(minutes) <= 59):
    raise InvalidInputError("time out of range")
  if schedule_type == "daily":
    if "day" in schedule:
      raise InvalidInputError("daily schedule must not include day")
    return {"type": schedule_type, "time": time_value}
  if schedule_type in ("weekly", "bi-weekly"):
    day = schedule.get("day")
    if not isinstance(day, int) or not 0 <= day <= 6:
      raise InvalidInputError("day must be weekday 0-6")
    return {"type": schedule_type, "day": day, "time": time_value}
  day = schedule.get("day")
  if not isinstance(day, int) or not 1 <= day <= 31:
    raise InvalidInputError("day must be day of month 1-31")
  return {"type": schedule_type, "day": day, "time": time_value}


def _parse_schedule(raw):
  try:
    schedule = json.loads(raw)
  except (TypeError, ValueError):
    schedule = None
  if isinstance(schedule, dict) and schedule.get("type") in _RECURRENCE_TYPES:
    try:
      return _validate_schedule(schedule)
    except InvalidInputError:
      pass
  return dict(_DEFAULT_SCHEDULE)


def get_backup_config():
  with db_connection() as connection:
    row = connection.execute(
      "SELECT enabled, schedule, updated_at FROM backup_config WHERE id = 1"
    ).fetchone()
  if row is None:
    return {
      "enabled": False,
      "schedule": dict(_DEFAULT_SCHEDULE),
      "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
  return {
    "enabled": bool(row["enabled"]),
    "schedule": _parse_schedule(row["schedule"]),
    "updated_at": row["updated_at"],
  }


def update_backup_config(enabled=None, schedule=None):
  updates = {}
  if enabled is not None:
    if not isinstance(enabled, bool):
      raise InvalidInputError("enabled must be a boolean")
    updates["enabled"] = 1 if enabled else 0
  if schedule is not None:
    updates["schedule"] = json.dumps(_validate_schedule(schedule))
  if not updates:
    raise InvalidInputError("nothing to update")
  updates["updated_at"] = datetime.now(timezone.utc).strftime(
    "%Y-%m-%d %H:%M:%S"
  )
  set_clause = ", ".join(f"{key} = ?" for key in updates)
  with db_transaction() as connection:
    connection.execute(
      f"UPDATE backup_config SET {set_clause} WHERE id = 1",
      tuple(updates.values()),
    )
  return get_backup_config()

import os

import config

from .data.backups import create_backup, get_backup_config
from .data.db import db_connection, db_transaction
from .exceptions.data.backups import BackupError
from .storage import apply_retention, save_backup_to_file


def _backup_dir():
  return os.environ.get("BACKUP_DIR", config.BACKUP_DIR)


def _max_backups():
  try:
    return int(os.environ.get("BACKUP_MAX_BACKUPS", config.BACKUP_MAX_BACKUPS))
  except ValueError:
    return config.BACKUP_MAX_BACKUPS


def run_backup_job(scheduled_at=None, user_id=None):
  """Run one scheduled backup: snapshot, persist to file, apply retention.

  Records backup_history with scheduled_at (NULL for manual run-now) and
  the stored file path. user_id stays NULL for scheduled runs (BKP-009).
  """
  backup = create_backup(user_id)
  try:
    path = save_backup_to_file(backup["data"], _backup_dir())
  except OSError as exc:
    raise BackupError(f"cannot persist backup: {exc}") from exc
  completed_at = backup["completed_at"]
  with db_transaction() as connection:
    connection.execute(
      """INSERT INTO backup_history (user_id, scheduled_at, completed_at, path)
         VALUES (?, ?, ?, ?)""",
      (user_id, scheduled_at, completed_at, path),
    )
  apply_retention(_backup_dir(), _max_backups())
  return {
    "filename": backup["filename"],
    "path": path,
    "scheduled_at": scheduled_at,
    "completed_at": completed_at,
  }


def next_scheduled_at(schedule, after=None):
  """Compute the next expected run time (naive local) for a schedule."""
  from datetime import datetime, timedelta

  after = after or datetime.now()
  time_part = schedule.get("time", "03:00")
  hours, minutes = (int(part) for part in time_part.split(":"))
  schedule_type = schedule.get("type", "weekly")

  def at_time(day):
    candidate = day.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    if candidate <= after:
      candidate += timedelta(days=1)
    return candidate

  if schedule_type == "daily":
    return at_time(after)
  if schedule_type == "weekly":
    step = 7
  elif schedule_type == "bi-weekly":
    step = 14
  else:  # monthly
    candidate = after.replace(
      hour=hours,
      minute=minutes,
      second=0,
      microsecond=0,
      day=min(schedule.get("day", 1), 28),
    )
    while candidate <= after:
      month = candidate.month + 1
      year = candidate.year + (month - 1) // 12
      candidate = candidate.replace(
        year=year, month=(month - 1) % 12 + 1
      )
    return candidate

  candidate = at_time(after)
  while candidate.weekday() != schedule.get("day", 6):
    candidate += timedelta(days=1)
  # at_time may have rolled a day; re-align to the weekday then add weeks
  while candidate <= after:
    candidate += timedelta(days=step)
  return candidate


def last_expected_run(schedule):
  """Most recent scheduled time at or before now (for missed detection)."""
  from datetime import datetime, timedelta

  now = datetime.now()
  nxt = next_scheduled_at(schedule, after=now)
  schedule_type = schedule.get("type", "weekly")
  if schedule_type == "daily":
    return nxt - timedelta(days=1)
  if schedule_type == "weekly":
    return nxt - timedelta(days=7)
  if schedule_type == "bi-weekly":
    return nxt - timedelta(days=14)
  month = (nxt.month - 2 - 1) % 12 + 1
  year = nxt.year + (nxt.month - 2 - 1) // 12
  return nxt.replace(year=year, month=month)


def get_last_completed_at():
  with db_connection() as connection:
    row = connection.execute(
      "SELECT scheduled_at FROM backup_history"
      " WHERE scheduled_at IS NOT NULL"
      " ORDER BY scheduled_at DESC LIMIT 1"
    ).fetchone()
  return row["scheduled_at"] if row else None


def should_catch_up():
  """True when a scheduled backup is enabled and the latest run is older
  than the last expected scheduled time (BKP-006/BKP-007)."""
  from datetime import datetime

  config = get_backup_config()
  if not config["enabled"]:
    return False
  last_completed = get_last_completed_at()
  if last_completed is None:
    return True
  try:
    last = datetime.strptime(last_completed, "%Y-%m-%d %H:%M:%S")
  except ValueError:
    return True
  return last < last_expected_run(config["schedule"])

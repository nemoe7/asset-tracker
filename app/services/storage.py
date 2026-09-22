import os

from app.services.exceptions.data.backups import BackupError


def ensure_location(backup_location):
  try:
    os.makedirs(backup_location, exist_ok=True)
  except OSError as exc:
    raise BackupError(f"cannot create backup location: {exc}") from exc


def save_backup_to_file(data, backup_location):
  ensure_location(backup_location)
  from datetime import datetime, timezone

  filename = f"backup-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.db"
  path = os.path.join(backup_location, filename)
  try:
    with open(path, "wb") as f:
      f.write(data)
  except OSError as exc:
    raise BackupError(f"cannot write backup file: {exc}") from exc
  return path


def apply_retention(backup_location, max_backups):
  try:
    files = [
      os.path.join(backup_location, name)
      for name in os.listdir(backup_location)
      if name.endswith(".db")
    ]
  except OSError as exc:
    raise BackupError(f"cannot list backup location: {exc}") from exc
  files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
  removed = 0
  for path in files[max_backups:]:
    try:
      os.remove(path)
      removed += 1
    except OSError as exc:
      raise BackupError(f"cannot remove old backup: {exc}") from exc
  return removed

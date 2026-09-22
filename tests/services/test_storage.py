import os

from app.services.storage import (
  BackupStorageError,
  apply_retention,
  ensure_location,
  save_backup_to_file,
)


def test_save_backup_to_file_writes_db(tmp_path):
  path = save_backup_to_file(b"sqlite-bytes", str(tmp_path))
  assert path.endswith(".db")
  with open(path, "rb") as f:
    assert f.read() == b"sqlite-bytes"


def test_save_backup_to_file_creates_missing_directory(tmp_path):
  location = str(tmp_path / "nested" / "backups")
  path = save_backup_to_file(b"data", location)
  assert os.path.isfile(path)


def test_apply_retention_keeps_newest_files(tmp_path):
  paths = []
  for i in range(5):
    p = tmp_path / f"backup-2026010{i}-000000.db"
    p.write_bytes(b"x")
    os.utime(p, (1_000_000 + i, 1_000_000 + i))
    paths.append(p)
  removed = apply_retention(str(tmp_path), 3)
  remaining = sorted(p.name for p in tmp_path.glob("*.db"))
  assert removed == 2
  assert remaining == [
    "backup-20260102-000000.db",
    "backup-20260103-000000.db",
    "backup-20260104-000000.db",
  ]


def test_apply_retention_under_limit_removes_nothing(tmp_path):
  (tmp_path / "backup-1.db").write_bytes(b"x")
  assert apply_retention(str(tmp_path), 10) == 0


def test_ensure_location_idempotent(tmp_path):
  target = tmp_path / "backups"
  ensure_location(str(target))
  ensure_location(str(target))
  assert target.is_dir()


def test_save_backup_rejects_unwritable_location(tmp_path):
  blocker = tmp_path / "file"
  blocker.write_bytes(b"not a dir")
  try:
    save_backup_to_file(b"data", str(blocker / "backups"))
  except BackupStorageError:
    pass
  else:
    raise AssertionError("expected BackupStorageError")

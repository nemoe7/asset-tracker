from unittest.mock import patch

import pytest

from app.services.data.backups import update_backup_config
from app.services.exceptions.data.backups import BackupError
from app.services.executor import run_backup_job


def test_run_backup_job_writes_file_and_records_history(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(
    enabled=True,
    schedule={"type": "weekly", "day": 6, "time": "03:00"},
  )
  scheduled_at = "2026-09-20 03:00:00"

  result = run_backup_job(scheduled_at)

  assert result["path"] is not None
  assert result["scheduled_at"] == scheduled_at
  with open(result["path"], "rb") as f:
    assert f.read().startswith(b"SQLite format 3\x00")


def test_run_backup_job_applies_retention(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  monkeypatch.setenv("BACKUP_MAX_BACKUPS", "2")
  update_backup_config(enabled=True)
  for i in range(3):
    (tmp_path / f"backup-2026010{i}-000000.db").write_bytes(b"old")
  run_backup_job("2026-09-20 03:00:00")
  names = sorted(p.name for p in tmp_path.glob("*.db"))
  assert len(names) == 2
  assert "backup-20260100-000000.db" not in names


def test_run_backup_job_records_scheduled_at_in_history(
  gen_test_data_admin, tmp_path, monkeypatch
):
  import app.services.data.db as db_module

  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  run_backup_job("2026-09-20 03:00:00")
  with db_module.db_connection() as connection:
    row = connection.execute(
      "SELECT scheduled_at, path, user_id FROM backup_history"
      " WHERE scheduled_at IS NOT NULL ORDER BY id DESC LIMIT 1"
    ).fetchone()
  assert row["scheduled_at"] == "2026-09-20 03:00:00"
  assert row["path"] is not None
  assert row["user_id"] is None


def test_run_backup_job_failure_raises_backup_error(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  with patch(
    "app.services.executor.create_backup", side_effect=BackupError()
  ):
    with pytest.raises(BackupError):
      run_backup_job("2026-09-20 03:00:00")

import os
from datetime import datetime, timedelta, timezone

import pytest

from app.services.data.backups import update_backup_config
from app.services.executor import last_expected_run, run_backup_job
from app.services.scheduler import (
  LOCK_FILENAME,
  _scheduled_job,
  check_and_run_missed_backups,
  init_backup_scheduler,
  start_scheduler,
  stop_scheduler,
)


def _backup_count():
  from app.services.data.db import db_connection

  with db_connection() as connection:
    return connection.execute("SELECT COUNT(*) FROM backup_history").fetchone()[0]


def _hold_lock(backup_location):
  """Write a fresh lock file, as a concurrent worker would."""
  (backup_location / LOCK_FILENAME).write_text("held")


def _hold_stale_lock(backup_location):
  lock = backup_location / LOCK_FILENAME
  lock.write_text("crashed")
  stale = datetime.now(timezone.utc) - timedelta(hours=2)
  os.utime(lock, (stale.timestamp(), stale.timestamp()))


def test_init_scheduler_registers_jobs_when_enabled(gen_test_data_admin):
  update_backup_config(
    enabled=True,
    schedule={"type": "weekly", "day": 6, "time": "03:00"},
  )
  scheduler = init_backup_scheduler()
  try:
    start_scheduler(scheduler)
    jobs = scheduler.get_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "scheduled-backup"
  finally:
    stop_scheduler(scheduler)


def test_init_scheduler_skips_jobs_when_disabled(gen_test_data_admin):
  update_backup_config(enabled=False)
  scheduler = init_backup_scheduler()
  try:
    start_scheduler(scheduler)
    assert scheduler.get_jobs() == []
  finally:
    stop_scheduler(scheduler)


def test_check_and_run_missed_backups_runs_when_stale(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(
    enabled=True,
    schedule={"type": "weekly", "day": 0, "time": "00:00"},
  )
  # A completed run older than the last expected scheduled time
  stale = last_expected_run({"type": "weekly", "day": 0, "time": "00:00"})
  stale -= __import__("datetime").timedelta(days=30)
  run_backup_job(scheduled_at=stale.strftime("%Y-%m-%d %H:%M:%S"))
  ran = check_and_run_missed_backups()
  assert ran is True


def test_check_and_run_missed_backups_noop_when_current(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  run_backup_job(scheduled_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
  assert check_and_run_missed_backups() is False


def test_check_and_run_missed_backups_noop_when_disabled(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=False)
  assert check_and_run_missed_backups() is False


def test_check_and_run_missed_backups_avoids_duplicates(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  check_and_run_missed_backups()
  count_first = check_and_run_missed_backups()
  # Second call within the same scheduled period must not back up again
  assert count_first is False


def test_scheduler_handles_missing_or_invalid_config(gen_test_data_admin):
  import app.services.data.db as db_module

  with db_module.db_transaction() as connection:
    connection.execute("UPDATE backup_config SET schedule = 'not-json' WHERE id = 1")
  scheduler = init_backup_scheduler()
  try:
    start_scheduler(scheduler)
    # invalid config treated as defaults; weekly schedule registered
    assert len(scheduler.get_jobs()) == 0  # enabled defaults to 0
  finally:
    stop_scheduler(scheduler)


def test_catch_up_skipped_while_another_worker_holds_lock(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  _hold_lock(tmp_path)

  before = _backup_count()
  ran = check_and_run_missed_backups()

  assert ran is False
  assert _backup_count() == before


def test_scheduled_job_skipped_while_another_worker_holds_lock(
  gen_test_data_admin, tmp_path, monkeypatch
):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  _hold_lock(tmp_path)

  before = _backup_count()
  _scheduled_job()

  assert _backup_count() == before
  # The other worker's lock is left in place.
  assert (tmp_path / LOCK_FILENAME).exists()


def test_lock_released_after_backup(gen_test_data_admin, tmp_path, monkeypatch):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)

  assert check_and_run_missed_backups() is True
  assert not (tmp_path / LOCK_FILENAME).exists()


def test_stale_lock_is_taken_over(gen_test_data_admin, tmp_path, monkeypatch):
  monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
  update_backup_config(enabled=True)
  _hold_stale_lock(tmp_path)

  ran = check_and_run_missed_backups()

  assert ran is True
  assert not (tmp_path / LOCK_FILENAME).exists()

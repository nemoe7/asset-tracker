import logging
import os
from contextlib import contextmanager

from apscheduler.schedulers.background import BackgroundScheduler

from .data.backups import get_backup_config
from .executor import backup_dir, run_backup_job

logger = logging.getLogger(__name__)

JOB_ID = "scheduled-backup"
LOCK_FILENAME = "backup.lock"
LOCK_STALE_SECONDS = 3600


def _lock_path():
  return os.path.join(backup_dir(), LOCK_FILENAME)


def _create_lock_file(path):
  from datetime import datetime, timezone

  descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)

  try:
    os.write(
      descriptor,
      datetime.now(timezone.utc).isoformat().encode(),
    )
  finally:
    os.close(descriptor)


def _acquire_lock(path):
  """Create the lock file. A stale file from a crashed process is taken
  over. Returns False when the lock is held by a live process."""
  from datetime import datetime, timezone

  try:
    _create_lock_file(path)
  except FileExistsError:
    acquired_at = datetime.fromtimestamp(
      os.path.getmtime(path),
      tz=timezone.utc,
    )
    age = (datetime.now(timezone.utc) - acquired_at).total_seconds()

    if age < LOCK_STALE_SECONDS:
      return False

    logger.warning("taking over stale backup lock at %s", path)
    os.unlink(path)
    _create_lock_file(path)

  return True


@contextmanager
def _backup_lock():
  """Exclusive lock that keeps a second worker from running a backup at
  the same time as the first (CON-001)."""
  path = _lock_path()
  os.makedirs(os.path.dirname(path), exist_ok=True)

  if not _acquire_lock(path):
    yield False
    return

  try:
    yield True
  finally:
    try:
      os.unlink(path)
    except FileNotFoundError:
      pass


def _seconds_until_next_run(schedule):
  from datetime import datetime

  from .executor import next_scheduled_at

  delta = next_scheduled_at(schedule) - datetime.now()
  return max(1.0, delta.total_seconds())


def init_backup_scheduler():
  """Build a scheduler whose single job is re-armed from backup_config."""
  scheduler = BackgroundScheduler(daemon=True)
  config = get_backup_config()
  if config["enabled"]:
    scheduler.add_job(
      _scheduled_job,
      trigger="interval",
      seconds=_seconds_until_next_run(config["schedule"]),
      id=JOB_ID,
      replace_existing=True,
      max_instances=1,
      kwargs={"scheduled_at": None},
    )
  return scheduler


def start_scheduler(scheduler):
  scheduler.start()


def stop_scheduler(scheduler):
  if scheduler.running:
    scheduler.shutdown(wait=False)


def _scheduled_job(scheduled_at=None):
  from datetime import datetime

  config = get_backup_config()
  if not config["enabled"]:
    return

  with _backup_lock() as acquired:
    if not acquired:
      logger.info("backup already running elsewhere; skipping scheduled run")
      return

    run_backup_job(
      scheduled_at=scheduled_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )


def check_and_run_missed_backups():
  """Run a catch-up backup when the last scheduled run is stale (BKP-006/007).

  Returns True when a catch-up backup was executed.
  """
  from .executor import should_catch_up

  if not should_catch_up():
    return False

  with _backup_lock() as acquired:
    if not acquired:
      logger.info("backup already running elsewhere; skipping catch-up")
      return False

    logger.info("missed scheduled backup detected; running catch-up backup")

    from .executor import last_expected_run

    config = get_backup_config()
    missed = last_expected_run(config["schedule"])
    run_backup_job(scheduled_at=missed.strftime("%Y-%m-%d %H:%M:%S"))

  return True

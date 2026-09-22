import logging

from apscheduler.schedulers.background import BackgroundScheduler

from .data.backups import get_backup_config
from .executor import run_backup_job

logger = logging.getLogger(__name__)

JOB_ID = "scheduled-backup"


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
  run_backup_job(
    scheduled_at=scheduled_at
    or datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  )


def check_and_run_missed_backups():
  """Run a catch-up backup when the last scheduled run is stale (BKP-006/007).

  Returns True when a catch-up backup was executed.
  """
  from .executor import should_catch_up

  if not should_catch_up():
    return False
  logger.info("missed scheduled backup detected; running catch-up backup")
  from datetime import datetime

  from .executor import last_expected_run

  config = get_backup_config()
  missed = last_expected_run(config["schedule"])
  run_backup_job(scheduled_at=missed.strftime("%Y-%m-%d %H:%M:%S"))
  return True

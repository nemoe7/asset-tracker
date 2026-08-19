from datetime import datetime
from zoneinfo import ZoneInfo

MANILA = ZoneInfo("Asia/Manila")
UTC = ZoneInfo("UTC")


def format_datetime(value):
  if not value:
    return ""

  if isinstance(value, str):
    value = datetime.fromisoformat(value)

  if value.tzinfo is None:
    value = value.replace(tzinfo=UTC)

  value = value.astimezone(MANILA)

  return value.strftime("%Y-%m-%d %H:%M:%S")

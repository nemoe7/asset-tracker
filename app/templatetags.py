import os
from datetime import date, datetime
from zoneinfo import ZoneInfo

DISPLAY_TZ = ZoneInfo(os.getenv("TZ", "Asia/Manila"))
UTC = ZoneInfo("UTC")


def format_datetime(value):
  if not value:
    return ""

  if isinstance(value, str):
    value = datetime.fromisoformat(value)

  if value.tzinfo is None:
    value = value.replace(tzinfo=UTC)

  value = value.astimezone(DISPLAY_TZ)

  return value.strftime("%Y-%m-%d %H:%M:%S")


def format_custom_field_value(value, field_type, today=None):
  if value is None or value == "":
    return value

  if field_type == "expiry_date" and value:
    try:
      expiry = date.fromisoformat(value)
    except ValueError:
      return value

    today = today or datetime.now(tz=UTC).date()

    if today >= expiry:
      return "Expired"

    days_left = (expiry - today).days
    day_word = "day" if days_left == 1 else "days"
    return f"Expires in {days_left} {day_word} [{value}]"

  return value

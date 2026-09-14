from datetime import datetime, timezone

from app.templatetags import format_custom_field_value


def test_expiry_date_future_shows_days_left():
  today = datetime(2026, 9, 14, tzinfo=timezone.utc).date()
  assert (
    format_custom_field_value("2026-09-15", "expiry_date", today=today)
    == "Expires in 1 day [2026-09-15]"
  )
  assert (
    format_custom_field_value("2026-09-16", "expiry_date", today=today)
    == "Expires in 2 days [2026-09-16]"
  )


def test_expiry_date_past_shows_expired():
  assert format_custom_field_value("2020-01-01", "expiry_date") == "Expired"


def test_expiry_date_today_shows_expired():
  today = datetime.now(tz=timezone.utc).date().isoformat()
  assert format_custom_field_value(today, "expiry_date") == "Expired"


def test_expiry_date_invalid_value_passes_through():
  assert format_custom_field_value("not-a-date", "expiry_date") == "not-a-date"


def test_expiry_date_empty_passes_through():
  assert format_custom_field_value("", "expiry_date") == ""
  assert format_custom_field_value(None, "expiry_date") is None


def test_non_expiry_type_passes_through():
  assert format_custom_field_value("hello", "text") == "hello"
  assert format_custom_field_value("2026-08-20", "date") == "2026-08-20"
  assert format_custom_field_value(5, "integer") == 5

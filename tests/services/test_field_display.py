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


def test_user_type_resolves_to_display_name(gen_test_data_admin):
  from app.services.data.users import create_user

  user_id = create_user("display_user", "display123", "Display User")
  assert format_custom_field_value(str(user_id), "user") == "Display User"


def test_user_type_without_name_resolves_to_username(gen_test_data_admin):
  from app.services.data.users import create_user

  create_user("nameless_user", "nameless123", None)

  assert format_custom_field_value("2", "user") == "nameless_user"


def test_user_type_unknown_id_passes_through():
  assert format_custom_field_value("424242", "user") == "424242"


def test_user_type_none_passes_through():
  assert format_custom_field_value(None, "user") is None
  assert format_custom_field_value("", "user") == ""

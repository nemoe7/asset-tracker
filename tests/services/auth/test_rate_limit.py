import time

from app.services.auth import rate_limit


def test_records_below_threshold_do_not_limit():
  rate_limit.reset()

  for _ in range(4):
    rate_limit.record_failure("1.2.3.4", username="alice")

  assert rate_limit.is_limited("1.2.3.4", username="alice") is False


def test_limit_blocks_after_max_failures():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  assert rate_limit.is_limited("1.2.3.4", username="alice") is True


def test_addresses_are_tracked_independently():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  assert rate_limit.is_limited("5.6.7.8", username="bob") is False


def test_clear_removes_limit():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  rate_limit.clear("1.2.3.4", username="alice")

  assert rate_limit.is_limited("1.2.3.4", username="alice") is False


def test_failures_outside_window_do_not_count(monkeypatch):
  rate_limit.reset()

  now = time.time()

  monkeypatch.setattr(rate_limit.time, "time", lambda: now)

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  monkeypatch.setattr(
    rate_limit.time,
    "time",
    lambda: now + rate_limit._WINDOW_SECONDS + 1,
  )

  assert rate_limit.is_limited("1.2.3.4", username="alice") is False


def test_composite_key_same_ip_different_users():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  assert rate_limit.is_limited("1.2.3.4", username="alice") is True
  assert rate_limit.is_limited("1.2.3.4", username="bob") is False


def test_composite_key_different_ip_same_user():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4", username="alice")

  assert rate_limit.is_limited("1.2.3.4", username="alice") is True
  assert rate_limit.is_limited("5.6.7.8", username="alice") is False
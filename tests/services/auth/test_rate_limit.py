import time

from app.services.auth import rate_limit


def test_records_below_threshold_do_not_limit():
  rate_limit.reset()

  for _ in range(4):
    rate_limit.record_failure("1.2.3.4")

  assert rate_limit.is_limited("1.2.3.4") is False


def test_limit_blocks_after_max_failures():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4")

  assert rate_limit.is_limited("1.2.3.4") is True


def test_addresses_are_tracked_independently():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4")

  assert rate_limit.is_limited("5.6.7.8") is False


def test_clear_removes_limit():
  rate_limit.reset()

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4")

  rate_limit.clear("1.2.3.4")

  assert rate_limit.is_limited("1.2.3.4") is False


def test_failures_outside_window_do_not_count(monkeypatch):
  rate_limit.reset()

  now = time.time()

  monkeypatch.setattr(rate_limit.time, "time", lambda: now)

  for _ in range(5):
    rate_limit.record_failure("1.2.3.4")

  monkeypatch.setattr(
    rate_limit.time,
    "time",
    lambda: now + rate_limit._WINDOW_SECONDS + 1,
  )

  assert rate_limit.is_limited("1.2.3.4") is False
import logging
import re
import secrets
import threading

_thread_local = threading.local()
_routes_thread_hex = secrets.token_hex(4)


class HealthCheckFilter(logging.Filter):
  def filter(self, record):
    return '"GET /health ' not in record.getMessage()


class RepeatHandler(logging.StreamHandler):
  def __init__(self):
    super().__init__()
    self.previous = None
    self.previous_record = None
    self.repeat_count = 0
    self._lock = threading.Lock()

  def emit(self, record: logging.LogRecord) -> None:
    with self._lock:
      self._emit(record)

  def _emit(self, record: logging.LogRecord) -> None:
    message = re.sub(
      r" ?\[\d{2}/[A-Za-z]{3}/\d{4} \d{2}:\d{2}:\d{2}\] ?",
      " ",
      record.getMessage(),
    ).strip()

    normalized = re.sub(
      r"\[[^]]+\]",
      "[TIMESTAMP]",
      message,
    )

    current = (
      record.name,
      record.levelno,
      normalized,
    )

    if current == self.previous:
      self.repeat_count += 1
      self.previous_record = record
      return

    if self.repeat_count:
      repeat_record = logging.makeLogRecord(self.previous_record.__dict__.copy())
      repeat_record.msg = (
        f"{self.previous_record.getMessage()} ({self.repeat_count + 1})"
      )
      repeat_record.args = ()

      repeat_record.msg = re.sub(
        r"\[\d{2}/[A-Za-z]{3}/\d{4} \d{2}:\d{2}:\d{2}\] ",
        "",
        repeat_record.msg,
      )

      super().emit(repeat_record)

    self.previous = current
    self.previous_record = record
    self.repeat_count = 0

    record.msg = message
    record.args = ()

    # First occurrence is emitted immediately.
    super().emit(record)


class ShortLevelFormatter(logging.Formatter):
  """
  Custom logging formatter that replaces "WARNING" with "WARN"
  and groups Flask request logs under a single random ID.
  """

  def format(self, record: logging.LogRecord) -> str:
    if record.levelname == "WARNING":
      record.levelname = "WARN"

    if record.name == "routes" or record.name.startswith("routes."):
      record.thread_hex = _routes_thread_hex
    else:
      if not hasattr(_thread_local, "thread_hex"):
        _thread_local.thread_hex = secrets.token_hex(2)

      record.thread_hex = _thread_local.thread_hex

    return super().format(record)


def configure_logging(show_logger_name=False):
  werkzeug_logger = logging.getLogger("werkzeug")

  handler = RepeatHandler()

  fmt = f"[%(asctime)s.%(msecs)03d] [%(thread_hex)s] %(levelname)-5s {'%(name)s: ' if show_logger_name else ''}%(message)s"

  handler.setFormatter(
    ShortLevelFormatter(
      fmt,
      "%Y-%m-%d %H:%M:%S",
    )
  )

  werkzeug_logger.handlers.clear()
  werkzeug_logger.addHandler(handler)
  werkzeug_logger.setLevel(logging.INFO)
  werkzeug_logger.propagate = False

  werkzeug_logger.addFilter(HealthCheckFilter())

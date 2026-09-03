import threading
import time

# In-memory login rate limiting: after too many failed logins from one
# address within the window, further attempts are rejected until the window
# slides past the failures. State is process-local and wiped on restart,
# which is acceptable for this deployment.
_MAX_FAILURES = 5
_WINDOW_SECONDS = 15 * 60

_lock = threading.Lock()
_failures = {}


def _prune(timestamps, now):
  cutoff = now - _WINDOW_SECONDS

  return [timestamp for timestamp in timestamps if timestamp > cutoff]


def is_limited(remote_addr):
  with _lock:
    timestamps = _prune(_failures.get(remote_addr, []), time.time())

    if timestamps:
      _failures[remote_addr] = timestamps
    else:
      _failures.pop(remote_addr, None)

    return len(timestamps) >= _MAX_FAILURES


def record_failure(remote_addr):
  with _lock:
    timestamps = _prune(_failures.get(remote_addr, []), time.time())

    timestamps.append(time.time())
    _failures[remote_addr] = timestamps


def clear(remote_addr):
  with _lock:
    _failures.pop(remote_addr, None)


def reset():
  with _lock:
    _failures.clear()
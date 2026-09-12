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


def _key(remote_addr, username):
  if username:
    return (remote_addr, username)

  return (remote_addr, "")


def is_limited(remote_addr, username=None):
  key = _key(remote_addr, username)

  with _lock:
    timestamps = _prune(_failures.get(key, []), time.time())

    if timestamps:
      _failures[key] = timestamps
    else:
      _failures.pop(key, None)

    return len(timestamps) >= _MAX_FAILURES


def record_failure(remote_addr, username=None):
  key = _key(remote_addr, username)

  with _lock:
    timestamps = _prune(_failures.get(key, []), time.time())

    timestamps.append(time.time())
    _failures[key] = timestamps


def clear(remote_addr, username=None):
  key = _key(remote_addr, username)

  with _lock:
    _failures.pop(key, None)


def reset():
  with _lock:
    _failures.clear()

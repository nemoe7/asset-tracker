from contextvars import ContextVar

_current_user_id = ContextVar(
  "current_user_id",
  default=None,
)


def set_current_user(user_id):
  return _current_user_id.set(user_id)


def get_current_user():
  return _current_user_id.get()


def reset_current_user(token):
  _current_user_id.reset(token)

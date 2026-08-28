from functools import wraps

from flask import (
  redirect,
  session,
  url_for,
)

from ..data.db import db_connection
from ..data.setup import is_first_run
from ..data.users import get_user
from .context import (
  reset_current_user,
  set_current_user,
)


def login_required(view):
  @wraps(view)
  def wrapped_view(*args, **kwargs):
    if is_first_run():
      return redirect(url_for("auth.setup"))

    user_id = session.get("user_id")

    if user_id is None:
      return redirect(url_for("auth.login"))

    with db_connection():
      user = get_user(user_id)

    if user is None:
      session.clear()
      return redirect(url_for("auth.login"))

    token = set_current_user(user["id"])

    try:
      return view(*args, **kwargs)
    finally:
      reset_current_user(token)

  return wrapped_view

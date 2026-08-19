from functools import wraps

from flask import (
  redirect,
  session,
  url_for,
)

from app.db import get_db


def login_required(view):
  @wraps(view)
  def wrapped_view(*args, **kwargs):
    user_id = session.get("user_id")

    if user_id is None:
      return redirect(url_for("auth.login"))

    connection = get_db()

    try:
      user = connection.execute(
        """
        SELECT id
        FROM users
        WHERE id = ?
          AND archived_at IS NULL
        """,
        (user_id,),
      ).fetchone()
    finally:
      connection.close()

    if user is None:
      session.clear()
      return redirect(url_for("auth.login"))

    return view(*args, **kwargs)

  return wrapped_view

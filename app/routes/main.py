from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  send_from_directory,
  session,
  url_for,
)

from app.db import get_db
from app.routes.auth import login_required
from app.services.inventory import get_items

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
  if current_app.config["FIRST_RUN"]:
    return redirect(url_for("auth.setup"))

  user_id = session.get("user_id")

  if user_id is None:
    return redirect(url_for("auth.login"))

  connection = get_db()

  try:
    user = connection.execute(
      """
      SELECT username
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

  items = get_items()

  return render_template(
    "index.jinja",
    items=items,
    search="",
    page=1,
    total_pages=1,
    username=user["username"],
  )


@main.route("/sw.js")
def service_worker():
  assert current_app.static_folder is not None

  return send_from_directory(
    current_app.static_folder,
    "sw.js",
    mimetype="application/javascript",
  )

from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  request,
  send_from_directory,
  session,
  url_for,
)

from app.auth import login_required
from app.db import get_db
from app.services.inventory import get_items
from app.services.locations import get_locations

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

  search = request.args.get("search", "").strip()

  items = get_items(
    search=search,
  )

  locations = get_locations()

  return render_template(
    "index.jinja",
    items=items,
    locations=locations,
    search=search,
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

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

from ..services.auth.authorization import check_permission
from ..services.data.db import get_db
from ..services.data.inventory import get_items
from ..services.data.locations import get_locations
from ..services.data.setup import (
  is_first_run,
)
from .auth import login_required

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
  if is_first_run():
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
  include_archived = request.args.get("include_archived") == "true"
  items = get_items(
    search=search,
    include_archived=include_archived,
  )

  locations = get_locations()

  can_manage_users = check_permission(
    user_id,
    "users.manage",
  )

  return render_template(
    "inventory/index.jinja",
    items=items,
    locations=locations,
    search=search,
    page=1,
    total_pages=1,
    username=user["username"],
    can_manage_users=can_manage_users,
  )


@main.route("/sw.js")
def service_worker():
  assert current_app.static_folder is not None

  return send_from_directory(
    current_app.static_folder,
    "sw.js",
    mimetype="application/javascript",
  )


@main.route("/health")
def health():
  return "", 200

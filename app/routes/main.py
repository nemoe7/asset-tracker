from flask import (
  Blueprint,
  current_app,
  render_template,
  request,
  send_from_directory,
)

from ..services.auth.authorization import check_permission
from ..services.auth.context import get_current_user
from ..services.data.inventory import get_items
from ..services.data.users import get_user
from .auth import login_required

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
  user_id = get_current_user()
  user = get_user(user_id)

  search = request.args.get("search", "").strip()
  include_archived = request.args.get("include_archived") == "true"

  items = get_items(
    search=search,
    include_archived=include_archived,
  )

  can_manage_users = check_permission(
    user_id,
    "users.manage",
  )

  return render_template(
    "inventory/index.jinja",
    items=items,
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

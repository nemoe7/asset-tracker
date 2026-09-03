from flask import (
  Blueprint,
  current_app,
  render_template,
  send_from_directory,
  session,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import check_permission

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
  user_id = session.get("user_id")

  return render_template(
    "inventory/index.jinja",
    username=session.get("username"),
    can_manage_locations=check_permission(user_id, "locations.manage"),
    can_manage_custom_fields=check_permission(user_id, "custom_fields.manage"),
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

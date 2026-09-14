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
    can_manage_locations=any(
      check_permission(user_id, permission_name)
      for permission_name in (
        "locations.create",
        "locations.update",
        "locations.delete",
      )
    ),
    can_manage_custom_fields=any(
      check_permission(user_id, permission_name)
      for permission_name in ("field.create", "field.delete")
    ),
    can_view_audit=check_permission(user_id, "audit.read"),
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

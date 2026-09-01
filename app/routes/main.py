from flask import (
  Blueprint,
  current_app,
  render_template,
  send_from_directory,
  session,
)

from .auth import login_required

main = Blueprint("main", __name__)


@main.route("/")
@login_required
def index():
  return render_template("inventory/index.jinja", username=session.get("username"))


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

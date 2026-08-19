from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  send_from_directory,
  url_for,
)

from app.services.inventory import get_items

main = Blueprint("main", __name__)


@main.route("/")
def index():
  if current_app.config["FIRST_RUN"]:
    return redirect(url_for("auth.setup"))

  items = get_items()

  return render_template(
    "index.jinja",
    items=items,
    search="",
    page=1,
    total_pages=1,
  )


@main.route("/sw.js")
def service_worker():
  assert current_app.static_folder is not None

  return send_from_directory(
    current_app.static_folder,
    "sw.js",
    mimetype="application/javascript",
  )

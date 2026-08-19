from flask import Blueprint, current_app, render_template, send_from_directory

from app.services.inventory import get_items

main = Blueprint("main", __name__)


@main.route("/")
def index():
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

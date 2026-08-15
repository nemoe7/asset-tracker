from flask import Blueprint, current_app, render_template, send_from_directory

main = Blueprint("main", __name__)


@main.route("/")
def index():
  username = "Stan"
  items = ["Apple", "Banana", "Orange"]

  # return render_template("index.jinja", username=username, items=items)
  return render_template("index.jinja")


@main.route("/sw.js")
def service_worker():
  assert current_app.static_folder is not None
  return send_from_directory(
    current_app.static_folder, "sw.js", mimetype="application/javascript"
  )

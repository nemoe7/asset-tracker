from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  request,
  send_from_directory,
  url_for,
)
from werkzeug.security import generate_password_hash

from app.db import get_db
from app.services.inventory import get_items
from app.services.setup import is_first_run

main = Blueprint("main", __name__)


@main.route("/")
def index():
  if current_app.config["FIRST_RUN"]:
    return redirect(url_for("main.setup"))

  items = get_items()

  return render_template(
    "index.jinja",
    items=items,
    search="",
    page=1,
    total_pages=1,
  )


@main.route("/setup", methods=["GET"])
def setup():
  if not current_app.config["FIRST_RUN"]:
    return redirect(url_for("main.index"))

  return render_template("setup.jinja")


@main.route("/setup", methods=["POST"])
def setup_post():
  if not current_app.config["FIRST_RUN"]:
    return redirect(url_for("main.index"))

  username = request.form["username"].strip()
  password = request.form["password"]
  confirm_password = request.form["confirm_password"]

  if not username:
    return render_template(
      "setup.jinja",
      error="Username is required.",
      username=username,
    )

  if password != confirm_password:
    return render_template(
      "setup.jinja",
      error="Passwords do not match.",
      username=username,
    )

  connection = get_db()

  try:
    connection.execute(
      """
      INSERT INTO users (
        username,
        password_hash,
        created_at,
        updated_at
      )
      VALUES (?, ?, datetime('now'), datetime('now'))
      """,
      (
        username,
        generate_password_hash(password),
      ),
    )

    connection.commit()

  except Exception:
    connection.rollback()
    raise

  finally:
    connection.close()

  current_app.config["FIRST_RUN"] = is_first_run()

  return redirect(url_for("main.index"))


@main.route("/sw.js")
def service_worker():
  assert current_app.static_folder is not None

  return send_from_directory(
    current_app.static_folder,
    "sw.js",
    mimetype="application/javascript",
  )

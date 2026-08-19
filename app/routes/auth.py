from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  request,
  url_for,
)
from werkzeug.security import generate_password_hash

from app.db import get_db
from app.services.setup import is_first_run

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/setup", methods=["GET"])
def setup():
  if not current_app.config["FIRST_RUN"]:
    return redirect(url_for("main.index"))

  return render_template("setup.jinja")


@auth.route("/setup", methods=["POST"])
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

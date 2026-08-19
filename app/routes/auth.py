from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  request,
  session,
  url_for,
)
from werkzeug.security import (
  check_password_hash,
  generate_password_hash,
)

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
    cursor = connection.execute(
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

    user_id = cursor.lastrowid

  except Exception:
    connection.rollback()
    raise

  finally:
    connection.close()

  session.clear()
  session["user_id"] = user_id

  current_app.config["FIRST_RUN"] = is_first_run()

  return redirect(url_for("main.index"))


@auth.route("/login", methods=["GET"])
def login():
  if current_app.config["FIRST_RUN"]:
    return redirect(url_for("auth.setup"))

  if session.get("user_id") is not None:
    return redirect(url_for("main.index"))

  return render_template("login.jinja")


@auth.route("/login", methods=["POST"])
def login_post():
  if current_app.config["FIRST_RUN"]:
    return redirect(url_for("auth.setup"))

  username = request.form["username"].strip()
  password = request.form["password"]

  connection = get_db()

  try:
    user = connection.execute(
      """
      SELECT id, password_hash
      FROM users
      WHERE username = ?
        AND archived_at IS NULL
      """,
      (username,),
    ).fetchone()
  finally:
    connection.close()

  if user is None or not check_password_hash(
    user["password_hash"],
    password,
  ):
    return render_template(
      "login.jinja",
      error="Invalid username or password.",
      username=username,
    )

  session.clear()
  session.permanent = True
  session["user_id"] = user["id"]

  return redirect(url_for("main.index"))


@auth.route("/logout", methods=["POST"])
def logout():
  session.clear()

  return redirect(url_for("auth.login"))

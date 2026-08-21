import sqlite3

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

from ..auth import login_required
from ..services.data.db import get_db
from ..services.data.setup import is_first_run
from ..services.data.users import _validate_password, _validate_username
from ..services.exceptions.data.users import (
  InvalidPasswordError,
  InvalidUsernameError,
  UsernameAlreadyExistsError,
)

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
  display_name = request.form["display-name"].strip()
  password = request.form["password"]
  confirm_password = request.form["confirm_password"]

  try:
    _validate_username(username)
  except InvalidUsernameError as error:
    return render_template(
      "setup.jinja",
      error=str(error),
      display_name=display_name,
      username=username,
    )

  if password != confirm_password:
    return render_template(
      "setup.jinja",
      error="Passwords do not match.",
      username=username,
      display_name=display_name,
    )

  try:
    _validate_password(password)
  except InvalidPasswordError as error:
    return render_template(
      "setup.jinja",
      error=str(error),
      username=username,
      display_name=display_name,
    )

  connection = get_db()

  try:
    try:
      cursor = connection.execute(
        """
        INSERT INTO users (
          username,
          name,
          password_hash,
          created_at,
          updated_at
        )
        VALUES (?, ?, ?, datetime('now'), datetime('now'))
        """,
        (
          username,
          display_name,
          generate_password_hash(password),
        ),
      )

      user_id = cursor.lastrowid

      admin_role = connection.execute(
        """
        SELECT id
        FROM roles
        WHERE name = 'Admin'
        """
      ).fetchone()

      if admin_role is None:
        raise RuntimeError("Admin role is missing from the database.")

      connection.execute(
        """
        INSERT INTO user_roles (
          user_id,
          role_id
        )
        VALUES (?, ?)
        """,
        (
          user_id,
          admin_role["id"],
        ),
      )

      connection.commit()

    except sqlite3.IntegrityError as error:
      connection.rollback()

      if "users.username" in str(error):
        raise UsernameAlreadyExistsError() from error

      raise

    except Exception:
      connection.rollback()
      raise

  except UsernameAlreadyExistsError as error:
    return render_template(
      "setup.jinja",
      error=str(error),
      username=username,
      display_name=display_name,
    )

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
@login_required
def logout():
  session.clear()

  return redirect(url_for("auth.login"))

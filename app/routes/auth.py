from flask import (
  Blueprint,
  current_app,
  redirect,
  render_template,
  request,
  session,
  url_for,
)
from werkzeug.security import check_password_hash

from ..services.auth.authentication import login_required
from ..services.data.db import get_db
from ..services.data.setup import (
  create_initial_admin,
  is_first_run,
)
from ..services.exceptions.data.users import (
  InvalidPasswordError,
  InvalidUsernameError,
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

  if password != confirm_password:
    return render_template(
      "setup.jinja",
      error="Passwords do not match.",
      username=username,
      display_name=display_name,
    )

  try:
    user_id = create_initial_admin(
      username=username,
      name=display_name,
      password=password,
    )
  except (InvalidUsernameError, InvalidPasswordError) as error:
    return render_template(
      "setup.jinja",
      error=str(error),
      username=username,
      display_name=display_name,
    )

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

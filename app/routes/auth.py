from flask import (
  Blueprint,
  redirect,
  render_template,
  request,
  session,
  url_for,
)

from ..services.auth.authentication import login_required
from ..services.auth import rate_limit
from ..services.data.setup import (
  create_initial_admin,
  is_first_run,
)
from ..services.data.users import (
  get_user_by_username,
  verify_password,
)
from ..services.exceptions.data.users import (
  InvalidPasswordError,
  InvalidUsernameError,
)

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.route("/setup", methods=["GET"])
def setup():
  if not is_first_run():
    return redirect(url_for("main.index"))

  return render_template("auth/setup.jinja")


@auth.route("/setup", methods=["POST"])
def setup_post():
  if not is_first_run():
    return redirect(url_for("main.index"))

  username = request.form["username"].strip()
  display_name = request.form["display_name"].strip()
  password = request.form["password"]
  confirm_password = request.form["confirm_password"]

  if password != confirm_password:
    return render_template(
      "auth/setup.jinja",
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
      "auth/setup.jinja",
      error=str(error),
      username=username,
      display_name=display_name,
    )

  session.clear()
  session["user_id"] = user_id
  session["username"] = username

  return redirect(url_for("main.index"))


@auth.route("/login", methods=["GET"])
def login():
  if is_first_run():
    return redirect(url_for("auth.setup"))

  if session.get("user_id") is not None:
    return redirect(url_for("main.index"))

  return render_template("auth/login.jinja")


@auth.route("/login", methods=["POST"])
def login_post():
  if is_first_run():
    return redirect(url_for("auth.setup"))

  if rate_limit.is_limited(request.remote_addr):
    return render_template(
      "auth/login.jinja",
      error="Too many failed login attempts. Try again later.",
      username=request.form["username"].strip(),
    ), 429

  username = request.form["username"].strip()
  password = request.form["password"]

  user = get_user_by_username(username)

  if (
    user is None
    or user["archived_at"] is not None
    or not verify_password(user["id"], password)
  ):
    rate_limit.record_failure(request.remote_addr)

    return render_template(
      "auth/login.jinja",
      error="Invalid username or password.",
      username=username,
    )

  rate_limit.clear(request.remote_addr)

  session.clear()
  session.permanent = True
  session["user_id"] = user["id"]
  session["username"] = username

  return redirect(url_for("main.index"))


@auth.route("/logout", methods=["POST"])
@login_required
def logout():
  session.clear()

  return redirect(url_for("auth.login"))

from flask import (
  Blueprint,
  redirect,
  render_template,
  request,
  session,
  url_for,
)

from ..services.auth.authorization import permission_required
from ..services.data.users import (
  archive_user,
  create_user,
  get_user_by_username,
  get_users,
  restore_user,
  update_user,
)
from ..services.exceptions.data.users import (
  InvalidPasswordError,
  InvalidUsernameError,
  UsernameAlreadyExistsError,
)
from .auth import login_required

admin = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
)


@admin.route("/users", methods=["GET"])
@login_required
@permission_required("users.manage")
def users():
  return render_template(
    "admin/users.jinja",
    users=get_users(),
  )


@admin.route("/users", methods=["POST"])
@login_required
@permission_required("users.manage")
def create_user_route():
  username = request.form["username"].strip()
  display_name = request.form["display_name"].strip()
  password = request.form["password"]

  try:
    create_user(
      username=username,
      name=display_name,
      password=password,
    )
  except UsernameAlreadyExistsError as error:
    archived_user = get_user_by_username(
      username,
      include_archived=True,
    )

    if archived_user is None:
      return render_template(
        "admin/users.jinja",
        users=get_users(),
        error="Unable to restore archived user.",
        username=username,
        display_name=display_name,
      )

    return render_template(
      "admin/users.jinja",
      users=get_users(),
      error=str(error),
      username=username,
      archived_user=archived_user,
      display_name=display_name,
    )
  except (InvalidUsernameError, InvalidPasswordError) as error:
    return render_template(
      "admin/users.jinja",
      users=get_users(),
      error=str(error),
      username=username,
      display_name=display_name,
    )

  return redirect(url_for("admin.users"))


@admin.route("/users/<int:user_id>", methods=["POST"])
@login_required
@permission_required("users.manage")
def update_user_route(user_id):
  username = request.form.get("username")
  password = request.form.get("password")

  username = username.strip() if username is not None else None
  password = password or None

  try:
    updated = update_user(
      user_id=user_id,
      username=username,
      password=password,
    )
  except ValueError as error:
    return render_template(
      "admin/users.jinja",
      users=get_users(),
      error=str(error),
    )

  if not updated:
    return redirect(url_for("admin.users"))

  return redirect(url_for("admin.users"))


@admin.route("/users/<int:user_id>/archive", methods=["POST"])
@login_required
@permission_required("users.manage")
def archive_user_route(user_id):
  if user_id == session.get("user_id"):
    return redirect(url_for("admin.users"))

  archive_user(user_id)

  return redirect(url_for("admin.users"))


@admin.route("/users/<int:user_id>/restore", methods=["POST"])
@login_required
@permission_required("users.manage")
def restore_user_route(user_id):
  restore_user(user_id)

  return redirect(url_for("admin.users"))

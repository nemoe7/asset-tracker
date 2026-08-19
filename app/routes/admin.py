from flask import (
  Blueprint,
  flash,
  redirect,
  render_template,
  request,
  url_for,
)

from app.auth import login_required
from app.services.authorization import permission_required
from app.services.users import (
  archive_user,
  create_user,
  get_users,
  restore_user,
  update_user,
)

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
  password = request.form["password"]

  try:
    create_user(
      username=username,
      password=password,
    )
  except ValueError as error:
    return render_template(
      "admin/users.jinja",
      users=get_users(),
      error=str(error),
      username=username,
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
  archive_user(user_id)

  return redirect(url_for("admin.users"))


@admin.route("/users/<int:user_id>/restore", methods=["POST"])
@login_required
@permission_required("users.manage")
def restore_user_route(user_id):
  restore_user(user_id)

  return redirect(url_for("admin.users"))

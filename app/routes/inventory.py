from flask import (
  Blueprint,
  redirect,
  request,
  url_for,
)

from ..services.data.inventory import (
  archive_item,
  create_item,
  update_item,
)
from .auth import login_required

inventory = Blueprint(
  "inventory",
  __name__,
  url_prefix="/inventory",
)


@inventory.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()
  location_id = request.form.get("location_id") or None

  if location_id is not None:
    location_id = int(location_id)

  try:
    create_item(
      name=name,
      location_id=location_id,
    )
  except ValueError:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>", methods=["POST"])
@login_required
def update(item_id):
  name = request.form.get("name", "").strip()
  location_id = request.form.get("location_id") or None

  if location_id is not None:
    location_id = int(location_id)

  try:
    updated = update_item(
      item_id,
      name=name,
      location_id=location_id,
    )
  except ValueError:
    return redirect(url_for("main.index"))

  if not updated:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/archive", methods=["POST"])
@login_required
def archive(item_id):
  archive_item(item_id)

  return redirect(url_for("main.index"))

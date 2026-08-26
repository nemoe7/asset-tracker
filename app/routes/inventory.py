from flask import (
  Blueprint,
  jsonify,
  redirect,
  request,
  url_for,
)

from ..services.data.inventory import (
  archive_item,
  create_item,
  get_item,
  restore_item,
  update_item,
)
from ..services.exceptions.data.inventory import InvalidItemNameError
from .auth import login_required

inventory = Blueprint(
  "inventory",
  __name__,
  url_prefix="/inventory",
)


@inventory.route("/<item_id>", methods=["GET"])
@login_required
def get(item_id):
  include_archived = request.args.get("include_archived") == "true"

  item = get_item(
    item_id,
    include_archived=include_archived,
  )

  if item is None:
    return jsonify(
      {
        "error": "Inventory item not found",
      }
    ), 404

  data = {
    "id": item["id"],
    "name": item["name"],
    "location_id": item["location_id"],
    "location_name": item["location_name"],
    "custom_fields": item["custom_fields"],
  }

  if include_archived:
    data["archived_at"] = item["archived_at"]

  return jsonify(data)


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
  except InvalidItemNameError:
    pass

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>", methods=["POST"])
@login_required
def update(item_id):
  name = request.form.get("name", "").strip()
  location_id = request.form.get("location_id") or None

  if location_id is not None:
    location_id = int(location_id)

  try:
    update_item(
      item_id,
      name=name,
      location_id=location_id,
    )
  except ValueError:
    return redirect(url_for("main.index"))

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/archive", methods=["POST"])
@login_required
def archive(item_id):
  archive_item(item_id)

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/restore", methods=["POST"])
@login_required
def restore(item_id):
  restore_item(item_id)

  return redirect(url_for("main.index"))

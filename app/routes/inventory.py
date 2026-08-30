import logging

from flask import (
  Blueprint,
  jsonify,
  redirect,
  render_template,
  request,
  url_for,
)

from app.services.checks import check_item
from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import get_custom_field_by_name

from ..services.data.inventory import (
  _UNSET,
  archive_item,
  create_item,
  get_item,
  get_items_paginated,
  restore_item,
  update_item,
)
from ..services.exceptions.data.common import InvalidInputError
from ..services.exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemIsNotArchivedError,
  ItemNotFoundError,
)
from ..services.exceptions.data.locations import LocationNotFoundError
from .auth import login_required

logger = logging.getLogger(__name__)

inventory = Blueprint(
  "inventory",
  __name__,
  url_prefix="/inventory",
)


@inventory.route("", methods=["GET"])
@login_required
def index():
  return redirect(url_for("main.index"))


@inventory.route("/fragment", methods=["GET"])
@login_required
def fragment():
  search = request.args.get("search")
  location_id = request.args.get("location_id")
  sort_by = request.args.get("sort_by", "name")
  sort_order = request.args.get("sort_order", "asc")
  include_archived = request.args.get("include_archived") == "true"

  try:
    if location_id == "__none__":
      location_id = None
    elif location_id:
      location_id = int(location_id)
    else:
      location_id = _UNSET
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 25))

    result = get_items_paginated(
      search=search,
      location_id=location_id,
      include_archived=include_archived,
      sort_by=sort_by,
      sort_order=sort_order,
      page=page,
      per_page=per_page,
    )
  except (InvalidInputError, ValueError) as error:
    return jsonify({"error": str(error)}), 400

  return render_template(
    "inventory/fragment.jinja",
    search=search,
    **result,
  )


@inventory.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()
  location_id = request.form.get("location_id")

  try:
    if location_id:
      item_id = create_item(
        name=name,
        location_id=int(location_id),
      )
    else:
      item_id = create_item(
        name=name,
      )
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except LocationNotFoundError as error:
    return jsonify({"error": str(error)}), 400

  if request.headers.get("Accept") == "application/json":
    return jsonify(
      {
        "id": item_id,
        "name": name,
      }
    )

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>", methods=["GET"])
@login_required
def get(item_id):
  include_archived = request.args.get("include_archived") == "true"

  item = get_item(
    item_id,
    include_archived=include_archived,
  )

  if item is None:
    return jsonify({"error": "Item does not exist"}), 404

  return jsonify(item)


@inventory.route("/<item_id>", methods=["POST"])
@login_required
def update(item_id):
  name = request.form.get("name", "").strip()

  if not name:
    name = _UNSET

  location_id = request.form.get("location_id")

  try:
    if location_id:
      location_id = int(location_id)
    else:
      location_id = None

    update_item(
      item_id,
      name=name,
      location_id=location_id,
    )

    for key, value in request.form.items():
      if key.startswith("f_"):
        field_name = key[2:]
        field = get_custom_field_by_name(field_name)

        if field is None:
          continue

        set_custom_field_value(
          item_id,
          field["id"],
          value,
        )
  except (InvalidInputError, ValueError, LocationNotFoundError) as error:
    return jsonify({"error": str(error)}), 400
  except ItemNotFoundError as error:
    return jsonify({"error": str(error)}), 404

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/archive", methods=["POST"])
@login_required
def archive(item_id):
  try:
    archive_item(item_id)
  except ItemNotFoundError as error:
    return jsonify({"error": str(error)}), 404
  except ItemIsArchivedError as error:
    return jsonify({"error": str(error)}), 400

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/restore", methods=["POST"])
@login_required
def restore(item_id):
  try:
    restore_item(item_id)
  except ItemNotFoundError as error:
    return jsonify({"error": str(error)}), 404
  except ItemIsNotArchivedError as error:
    return jsonify({"error": str(error)}), 400

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/check", methods=["POST"])
@login_required
def check(item_id):
  try:
    item = check_item(item_id)
  except ItemNotFoundError as error:
    return jsonify({"error": str(error)}), 404
  except ItemIsArchivedError as error:
    return jsonify({"error": str(error)}), 400

  return jsonify(item)

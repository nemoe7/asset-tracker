import logging
from datetime import datetime

from flask import (
  Blueprint,
  Response,
  jsonify,
  redirect,
  render_template,
  request,
  url_for,
)

from app.services.checks import check_item
from app.services.data.custom_field_filters import parse_filters
from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import get_custom_fields

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
from ..services.exceptions.data.custom_field_values import (
  RequiredCustomFieldError,
)
from ..services.exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemIsNotArchivedError,
  ItemNotFoundError,
)
from ..services.exceptions.data.locations import LocationNotFoundError
from ..services.export import build_export
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


def _parse_custom_field_filters():
  f_fields = request.args.getlist("f_field")
  f_ops = request.args.getlist("f_op")
  f_values = request.args.getlist("f_value")

  if not (len(f_fields) == len(f_ops) == len(f_values)):
    raise InvalidInputError("Malformed filter parameters")

  rows = [
    (field_id, op, value)
    for field_id, op, value in zip(f_fields, f_ops, f_values)
    if value != ""
  ]

  if not rows:
    return None, []

  fields = get_custom_fields()
  filters = parse_filters(
    [field_id for field_id, _op, _value in rows],
    [op for _field_id, op, _value in rows],
    [value for _field_id, _op, value in rows],
    fields,
  )

  fields_by_id = {field["id"]: field for field in fields}
  filtered_fields = []
  seen_ids = set()

  for field_id, _op, _value in filters:
    if field_id not in seen_ids:
      seen_ids.add(field_id)
      filtered_fields.append(fields_by_id[field_id])

  return filters, filtered_fields


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

    custom_field_filters, filtered_custom_fields = _parse_custom_field_filters()

    result = get_items_paginated(
      search=search,
      location_id=location_id,
      include_archived=include_archived,
      sort_by=sort_by,
      sort_order=sort_order,
      custom_field_filters=custom_field_filters,
      page=page,
      per_page=per_page,
    )
  except (InvalidInputError, ValueError) as error:
    return jsonify({"error": str(error)}), 400

  return render_template(
    "inventory/fragment.jinja",
    search=search,
    filtered_custom_fields=filtered_custom_fields,
    **result,
  )


def _coerce_form_value(field, raw_value):
  field_type = field["field_type"]

  if field_type == "integer":
    return int(raw_value)

  if field_type == "decimal":
    return float(raw_value)

  if field_type == "boolean":
    return raw_value == "true"

  return raw_value


def _collect_custom_field_values():
  return {
    key[2:]: value
    for key, value in request.form.items()
    if key.startswith("f_")
  }


def _required_custom_field_error(field):
  raise RequiredCustomFieldError(field["name"])


def _apply_custom_field_values(item_id, custom_fields, values):
  for field in custom_fields:
    raw_value = values.get(field["name"])

    if raw_value is None:
      continue

    if raw_value == "":
      set_custom_field_value(item_id, field["id"], None)
      continue

    set_custom_field_value(
      item_id,
      field["id"],
      _coerce_form_value(field, raw_value),
    )


@inventory.route("", methods=["POST"])
@login_required
def create():
  name = request.form.get("name", "").strip()
  description = request.form.get("description") or None
  location_id = request.form.get("location_id")

  custom_fields = [
    field
    for field in get_custom_fields()
    if field["field_type"] != "user"
  ]
  values = _collect_custom_field_values()

  try:
    for field in custom_fields:
      if field["required"] and not values.get(field["name"], "").strip():
        _required_custom_field_error(field)

    if location_id:
      item_id = create_item(
        name=name,
        description=description,
        location_id=int(location_id),
      )
    else:
      item_id = create_item(
        name=name,
        description=description,
      )

    _apply_custom_field_values(item_id, custom_fields, values)
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except LocationNotFoundError as error:
    return jsonify({"error": str(error)}), 400

  if request.headers.get("Accept") == "application/json":
    return jsonify(
      {
        "id": item_id,
        "name": name,
        "description": description,
        "location_id": location_id,
      }
    )

  return redirect(url_for("main.index"))


@inventory.route("/export", methods=["GET"])
@login_required
def export():
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

    custom_field_filters, _filtered_custom_fields = _parse_custom_field_filters()

    csv_data = build_export(
      search=search,
      location_id=location_id,
      include_archived=include_archived,
      sort_by=sort_by,
      sort_order=sort_order,
      custom_field_filters=custom_field_filters,
      field_keys=request.args.getlist("fields") or None,
    )
  except (InvalidInputError, ValueError) as error:
    return jsonify({"error": str(error)}), 400

  filename = datetime.now().strftime("inventory-export-%Y%m%d-%H%M.csv")

  return Response(
    csv_data,
    mimetype="text/csv",
    headers={
      "Content-Disposition": f'attachment; filename="{filename}"',
    },
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
    return jsonify({"error": "Item does not exist"}), 404

  return jsonify(item)


@inventory.route("/<item_id>", methods=["POST"])
@login_required
def update(item_id):
  name = request.form.get("name", "").strip()
  description = request.form.get("description")

  if not name:
    name = _UNSET

  location_id = request.form.get("location_id")

  if description == "":
    description = None

  custom_fields = [
    field
    for field in get_custom_fields()
    if field["field_type"] != "user"
  ]
  values = _collect_custom_field_values()

  try:
    for field in custom_fields:
      if field["required"] and values.get(field["name"], "") == "":
        _required_custom_field_error(field)

    if location_id:
      location_id = int(location_id)
    else:
      location_id = None

    update_item(
      item_id,
      name=name,
      description=description,
      location_id=location_id,
    )

    _apply_custom_field_values(item_id, custom_fields, values)
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

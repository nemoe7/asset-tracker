import logging
from datetime import datetime, timezone

from flask import (
  Blueprint,
  Response,
  jsonify,
  redirect,
  render_template,
  request,
  session,
  url_for,
)

from app.services.checks import check_item
from app.services.constants import UNSET as _UNSET
from app.services.data.custom_field_filters import parse_filters
from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import get_custom_fields

from ..services.auth.authentication import login_required
from ..services.auth.authorization import (
  check_permission,
  permission_required,
)
from ..services.data.inventory import (
  archive_item,
  create_item,
  get_item,
  get_items_paginated,
  import_items,
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
from ..services.import_svc import parse_import_file

logger = logging.getLogger(__name__)

inventory = Blueprint(
  "inventory",
  __name__,
  url_prefix="/inventory",
)

_MAX_PER_PAGE = 50


@inventory.route("", methods=["GET"])
@login_required
def index():
  return redirect(url_for("main.index"))


def _parse_custom_field_filters(readable_fields=None):
  f_fields = request.args.getlist("f_field")
  f_ops = request.args.getlist("f_op")
  f_values = request.args.getlist("f_value")

  # Rows are (field, op, value) triplets. Browsers omit empty form values,
  # so align by row index and drop incomplete or value-less rows entirely.
  rows = []

  for index, field_id in enumerate(f_fields):
    op = f_ops[index] if index < len(f_ops) else ""
    value = f_values[index] if index < len(f_values) else ""

    if field_id and value:
      rows.append((field_id, op, value))

  if not rows:
    return None, []

  if readable_fields is None:
    readable_fields = get_custom_fields()

  filters = parse_filters(
    [field_id for field_id, _op, _value in rows],
    [op for _field_id, op, _value in rows],
    [value for _field_id, _op, value in rows],
    readable_fields,
  )

  fields_by_id = {field["id"]: field for field in readable_fields}
  filtered_fields = []
  seen_ids = set()

  for field_id, _op, _value in filters:
    if field_id not in seen_ids:
      seen_ids.add(field_id)
      filtered_fields.append(fields_by_id[field_id])

  return filters, filtered_fields


def _visible_field_ids(user_id):
  return {
    field["id"]
    for field in get_custom_fields()
    if check_permission(user_id, f"field.{field['id']}.read")
  }


def _editable_field_ids(user_id):
  return {
    field["id"]
    for field in get_custom_fields()
    if check_permission(user_id, f"field.{field['id']}.update")
  }


@inventory.route("/fragment", methods=["GET"])
@login_required
def fragment():
  search = request.args.get("search")
  location_id = request.args.get("location_id")
  sort_by = request.args.get("sort_by", "name")
  sort_order = request.args.get("sort_order", "asc")
  include_archived = request.args.get("include_archived") == "true"

  user_id = session.get("user_id")
  visible_field_ids = _visible_field_ids(user_id)
  readable_fields = [
    field for field in get_custom_fields() if field["id"] in visible_field_ids
  ]

  try:
    if location_id == "__none__":
      location_id = None
    elif location_id:
      location_id = int(location_id)
    else:
      location_id = _UNSET
    page = int(request.args.get("page", 1))
    per_page = min(int(request.args.get("per_page", 25)), _MAX_PER_PAGE)

    custom_field_filters, filtered_custom_fields = _parse_custom_field_filters(
      readable_fields
    )

    result = get_items_paginated(
      search=search,
      location_id=location_id,
      include_archived=include_archived,
      sort_by=sort_by,
      sort_order=sort_order,
      custom_field_filters=custom_field_filters,
      visible_field_ids=visible_field_ids,
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

  try:
    if field_type == "integer":
      return int(raw_value)

    if field_type == "decimal":
      return float(raw_value)
  except ValueError:
    raise InvalidInputError(f"Invalid value for {field_type} field") from None

  if field_type == "boolean":
    return raw_value == "true"

  return raw_value


def _collect_custom_field_values():
  return {key[2:]: value for key, value in request.form.items() if key.startswith("f_")}


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

  editable_field_ids = _editable_field_ids(session.get("user_id"))
  custom_fields = [
    field
    for field in get_custom_fields()
    if field["field_type"] != "user" and field["id"] in editable_field_ids
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
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("main.index", error=str(error)))
  except LocationNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("main.index", error=str(error)))

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

  user_id = session.get("user_id")
  visible_field_ids = _visible_field_ids(user_id)
  readable_fields = [
    field for field in get_custom_fields() if field["id"] in visible_field_ids
  ]

  try:
    if location_id == "__none__":
      location_id = None
    elif location_id:
      location_id = int(location_id)
    else:
      location_id = _UNSET

    custom_field_filters, _filtered_custom_fields = _parse_custom_field_filters(
      readable_fields
    )

    csv_data = build_export(
      search=search,
      location_id=location_id,
      include_archived=include_archived,
      sort_by=sort_by,
      sort_order=sort_order,
      custom_field_filters=custom_field_filters,
      field_keys=request.args.getlist("fields") or None,
      visible_field_ids=visible_field_ids,
    )
  except (InvalidInputError, ValueError) as error:
    return jsonify({"error": str(error)}), 400

  filename = datetime.now(timezone.utc).strftime("asset-export-%Y%m%d-%H%M.csv")

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
    visible_field_ids=_visible_field_ids(session.get("user_id")),
  )

  if item is None:
    return jsonify({"error": "Asset does not exist"}), 404

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

  editable_field_ids = _editable_field_ids(session.get("user_id"))
  custom_fields = [
    field
    for field in get_custom_fields()
    if field["field_type"] != "user" and field["id"] in editable_field_ids
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
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("main.index", error=str(error)))
  except ItemNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("main.index", error=str(error)))

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/archive", methods=["POST"])
@login_required
def archive(item_id):
  try:
    archive_item(item_id)
  except ItemNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("main.index", error=str(error)))
  except ItemIsArchivedError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("main.index", error=str(error)))

  return redirect(url_for("main.index"))


@inventory.route("/<item_id>/restore", methods=["POST"])
@login_required
def restore(item_id):
  try:
    restore_item(item_id)
  except ItemNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("main.index", error=str(error)))
  except ItemIsNotArchivedError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("main.index", error=str(error)))

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


@inventory.route("/import", methods=["POST"])
@login_required
@permission_required("inventory.import")
def import_items_route():
  file = request.files.get("file")

  if file is None:
    return jsonify({"error": "No import file provided"}), 400

  try:
    rows = parse_import_file(file)
    result = import_items(
      rows,
      editable_field_ids=_editable_field_ids(session.get("user_id")),
    )
  except (InvalidInputError, LocationNotFoundError) as error:
    return jsonify({"error": str(error)}), 400

  return jsonify({"imported_count": result["imported_count"]})

from flask import (
  Blueprint,
  abort,
  jsonify,
  redirect,
  request,
  session,
  url_for,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import (
  check_permission,
  permission_required,
)
from ..services.data.custom_fields import (
  archive_custom_field,
  create_custom_field,
  get_custom_field,
  get_custom_fields,
  restore_custom_field,
  update_custom_field,
)
from ..services.exceptions.data.common import InvalidInputError
from ..services.exceptions.data.custom_fields import CustomFieldNotFoundError

custom_fields = Blueprint(
  "custom_fields",
  __name__,
  url_prefix="/custom-fields",
)


@custom_fields.route("", methods=["POST"])
@permission_required("field.create")
@login_required
def create():
  name = request.form.get("name", "").strip()
  field_type = request.form.get("field_type", "")

  try:
    field_id = create_custom_field(
      name=name,
      field_type=field_type,
    )
  except InvalidInputError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))

  if request.headers.get("Accept") == "application/json":
    return jsonify(
      {
        "id": field_id,
        "name": name,
        "field_type": field_type,
      }
    )

  return redirect(url_for("admin.settings", tab="custom-fields"))


@custom_fields.route("", methods=["GET"])
@login_required
def list():
  include_archived = request.args.get("include_archived") == "true"
  user_id = session.get("user_id")

  fields = []

  for field in get_custom_fields(
    include_archived=include_archived,
  ):
    if not check_permission(user_id, f"field.{field['id']}.read"):
      continue

    fields.append(
      {
        **field,
        "is_editable": check_permission(user_id, f"field.{field['id']}.update"),
      }
    )

  return jsonify(fields)


@custom_fields.route("/<int:field_id>", methods=["GET"])
@login_required
def get(field_id):
  user_id = session.get("user_id")

  if not check_permission(user_id, f"field.{field_id}.read"):
    abort(404)

  field = get_custom_field(field_id)

  if field is None:
    return jsonify({"error": "Custom field not found"}), 404

  return jsonify(field)


@custom_fields.route("/<int:field_id>", methods=["POST"])
@login_required
def update(field_id):
  user_id = session.get("user_id")

  if not check_permission(user_id, f"field.{field_id}.update"):
    abort(403)

  kwargs = {}

  if "name" in request.form:
    kwargs["name"] = request.form["name"].strip()

  if "field_type" in request.form:
    kwargs["field_type"] = request.form["field_type"]

  if "description" in request.form:
    kwargs["description"] = request.form["description"].strip() or None

  if "required" in request.form:
    kwargs["required"] = request.form["required"] == "true"

  if "enum_values" in request.form:
    kwargs["enum_values"] = [
      value.strip() for value in request.form["enum_values"].split(",") if value.strip()
    ]

  try:
    update_custom_field(
      field_id,
      **kwargs,
    )
  except InvalidInputError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))
  except CustomFieldNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))

  return redirect(url_for("admin.settings", tab="custom-fields"))


@custom_fields.route("/<int:field_id>/archive", methods=["POST"])
@permission_required("field.delete")
@login_required
def archive(field_id):
  try:
    archive_custom_field(field_id)
  except InvalidInputError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))
  except CustomFieldNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))

  return redirect(url_for("admin.settings", tab="custom-fields"))


@custom_fields.route("/<int:field_id>/restore", methods=["POST"])
@permission_required("field.create")
@login_required
def restore(field_id):
  try:
    restore_custom_field(field_id)
  except InvalidInputError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 400

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))
  except CustomFieldNotFoundError as error:
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": str(error)}), 404

    return redirect(url_for("admin.settings", tab="custom-fields", error=str(error)))

  return redirect(url_for("admin.settings", tab="custom-fields"))

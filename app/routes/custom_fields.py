from flask import (
  Blueprint,
  jsonify,
  redirect,
  request,
  url_for,
)

from ..services.auth.authentication import login_required
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
    return jsonify({"error": str(error)}), 400

  if request.headers.get("Accept") == "application/json":
    return jsonify(
      {
        "id": field_id,
        "name": name,
        "field_type": field_type,
      }
    )

  return redirect(url_for("main.index"))


@custom_fields.route("", methods=["GET"])
@login_required
def list():
  include_archived = request.args.get("include_archived") == "true"

  return jsonify(
    get_custom_fields(
      include_archived=include_archived,
    )
  )


@custom_fields.route("/<int:field_id>", methods=["GET"])
@login_required
def get(field_id):
  field = get_custom_field(field_id)

  if field is None:
    return jsonify({"error": "Custom field not found"}), 404

  return jsonify(field)


@custom_fields.route("/<int:field_id>", methods=["POST"])
@login_required
def update(field_id):
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
    return jsonify({"error": str(error)}), 400
  except CustomFieldNotFoundError as error:
    return jsonify({"error": str(error)}), 404

  return redirect(url_for("main.index"))


@custom_fields.route("/<int:field_id>/archive", methods=["POST"])
@login_required
def archive(field_id):
  try:
    archive_custom_field(field_id)
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except CustomFieldNotFoundError as error:
    return jsonify({"error": str(error)}), 404

  return redirect(url_for("main.index"))


@custom_fields.route("/<int:field_id>/restore", methods=["POST"])
@login_required
def restore(field_id):
  try:
    restore_custom_field(field_id)
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400
  except CustomFieldNotFoundError as error:
    return jsonify({"error": str(error)}), 404

  return redirect(url_for("main.index"))

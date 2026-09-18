from flask import (
  Blueprint,
  jsonify,
  request,
  session,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import check_permission
from ..services.data.export_templates import (
  create_export_template,
  get_export_templates,
)
from ..services.exceptions.data.export_templates import (
  InvalidExportTemplateConfigurationError,
  InvalidExportTemplateNameError,
)

export_templates = Blueprint(
  "export_templates",
  __name__,
  url_prefix="/export-templates",
)


@export_templates.route("", methods=["GET"])
@login_required
def list():
  user_id = session.get("user_id")

  return jsonify(get_export_templates(user_id))


@export_templates.route("", methods=["POST"])
@login_required
def create():
  user_id = session.get("user_id")

  body = request.get_json(silent=True) or {}
  shared = body.get("shared", False)

  if shared and not check_permission(user_id, "*"):
    return jsonify({"error": "Not allowed to create shared templates"}), 403

  try:
    template_id = create_export_template(
      user_id,
      body.get("name", ""),
      body.get("configuration", {}),
      shared=shared,
    )
  except (
    InvalidExportTemplateNameError,
    InvalidExportTemplateConfigurationError,
  ) as error:
    return jsonify({"error": str(error)}), 400

  return jsonify({"id": template_id, "shared": shared}), 201

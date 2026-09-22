from flask import (
  Blueprint,
  jsonify,
  redirect,
  request,
  session,
  url_for,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import check_permission
from ..services.data.export_templates import (
  create_export_template,
  delete_export_template,
  get_export_template,
  get_export_templates,
  update_export_template,
)
from ..services.exceptions.data.export_templates import (
  ExportTemplateAccessError,
  ExportTemplateNotFoundError,
  InvalidExportTemplateConfigurationError,
  InvalidExportTemplateNameError,
)

export_templates = Blueprint(
  "export_templates",
  __name__,
  url_prefix="/export-templates",
)


def _user_id():
  return session.get("user_id")


def _is_admin(user_id):
  return check_permission(user_id, "*")


def _error(status, message):
  return jsonify({"error": message}), status


@export_templates.route("", methods=["GET"])
@login_required
def list():
  return jsonify(get_export_templates(_user_id()))


@export_templates.route("", methods=["POST"])
@login_required
def create():
  user_id = _user_id()

  body = request.get_json(silent=True) or {}
  shared = body.get("shared", False)

  if shared and not _is_admin(user_id):
    return _error(403, "Not allowed to create shared templates")

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
    return _error(400, str(error))

  return jsonify({"id": template_id, "shared": shared}), 201


# GET (browser navigation from the export modal) and POST both work;
# apply is read-only and just redirects to /inventory/export.
@export_templates.route("/<int:template_id>/apply", methods=["GET", "POST"])
@login_required
def apply(template_id):
  try:
    template = get_export_template(template_id, _user_id())
  except ExportTemplateNotFoundError:
    return _error(404, "Export template does not exist")

  configuration = template["configuration"]
  params = {}

  filters = configuration.get("filters") or []
  if filters:
    params["f_field"] = [row[0] for row in filters]
    params["f_op"] = [row[1] for row in filters]
    params["f_value"] = [row[2] for row in filters]

  columns = configuration.get("columns") or []
  if columns:
    params["fields"] = columns

  return redirect(url_for("inventory.export", **params))


@export_templates.route("/<int:template_id>", methods=["PUT", "PATCH"])
@login_required
def update(template_id):
  user_id = _user_id()

  body = request.get_json(silent=True) or {}

  kwargs = {}

  if "name" in body:
    kwargs["name"] = body["name"]

  if "configuration" in body:
    kwargs["configuration"] = body["configuration"]

  try:
    template = update_export_template(
      template_id, user_id, allow_shared=_is_admin(user_id), **kwargs
    )
  except (
    InvalidExportTemplateNameError,
    InvalidExportTemplateConfigurationError,
  ) as error:
    return _error(400, str(error))
  except ExportTemplateNotFoundError as error:
    return _error(404, str(error))
  except ExportTemplateAccessError as error:
    return _error(403, str(error))

  return jsonify(template)


@export_templates.route("/<int:template_id>", methods=["DELETE"])
@login_required
def delete(template_id):
  try:
    delete_export_template(
      template_id,
      _user_id(),
      allow_shared=_is_admin(_user_id()),
    )
  except ExportTemplateNotFoundError as error:
    return _error(404, str(error))
  except ExportTemplateAccessError as error:
    return _error(403, str(error))

  return "", 204

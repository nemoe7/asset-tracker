from flask import (
  Blueprint,
  abort,
  redirect,
  render_template,
  request,
  session,
  url_for,
)

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
from ..services.data.locations import (
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)
from ..services.exceptions.data.common import InvalidInputError
from ..services.exceptions.data.custom_fields import (
  CustomFieldInUseError,
  CustomFieldNotFoundError,
)
from ..services.exceptions.data.locations import (
  LocationAlreadyExistsError,
  LocationNotFoundError,
)
from ..services.auth.authentication import login_required

admin = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
)

_LOCATION_TAB = "locations"
_CUSTOM_FIELDS_TAB = "custom-fields"
_BACKUPS_TAB = "backups"
_VALID_TABS = (
  _LOCATION_TAB,
  _CUSTOM_FIELDS_TAB,
  _BACKUPS_TAB,
)


def _render_settings(
  active_tab,
  error=None,
  **context,
):
  user_id = session.get("user_id")

  return render_template(
    "admin/settings.jinja",
    locations=get_locations(),
    custom_fields=get_custom_fields(),
    archived_custom_fields=get_custom_fields(include_archived=True),
    active_tab=active_tab,
    error=error,
    can_manage_locations=check_permission(user_id, "locations.manage"),
    can_manage_custom_fields=check_permission(user_id, "custom_fields.manage"),
    can_manage_backups=(
      check_permission(user_id, "backups.create")
      or check_permission(user_id, "backups.restore")
    ),
    **context,
  )


def _get_active_tab():
  tab = request.args.get("tab")

  if tab not in _VALID_TABS:
    return _LOCATION_TAB

  return tab


def _parse_enum_values(raw):
  if raw is None:
    return None

  values = [value.strip() for value in raw.split("\n") if value.strip()]

  if not values:
    return None

  return values


@admin.route("", methods=["GET"])
@login_required
def settings():
  active_tab = _get_active_tab()

  permission_by_tab = {
    _LOCATION_TAB: ("locations.manage",),
    _CUSTOM_FIELDS_TAB: ("custom_fields.manage",),
    _BACKUPS_TAB: ("backups.create", "backups.restore"),
  }

  if not any(
    check_permission(session.get("user_id"), permission_name)
    for permission_name in permission_by_tab[active_tab]
  ):
    abort(403)

  return _render_settings(active_tab)


@admin.route("/locations", methods=["POST"])
@login_required
@permission_required("locations.manage")
def create_location_route():
  name = request.form.get("name", "").strip()
  description = request.form.get("description") or None

  try:
    create_location(
      name=name,
      description=description,
    )
  except (InvalidInputError, LocationAlreadyExistsError) as error:
    return _render_settings(
      _LOCATION_TAB,
      error=str(error),
      location_name=name,
      location_description=request.form.get("description"),
    )

  return redirect(url_for("admin.settings", tab=_LOCATION_TAB))


@admin.route("/locations/<int:location_id>", methods=["POST"])
@login_required
@permission_required("locations.manage")
def update_location_route(location_id):
  name = request.form.get("name", "").strip()
  description = request.form.get("description") or None

  try:
    update_location(
      location_id,
      name=name,
      description=description,
    )
  except (InvalidInputError, LocationAlreadyExistsError) as error:
    return _render_settings(
      _LOCATION_TAB,
      error=str(error),
    )
  except LocationNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_LOCATION_TAB))


@admin.route("/locations/<int:location_id>/delete", methods=["POST"])
@login_required
@permission_required("locations.manage")
def delete_location_route(location_id):
  if get_location(location_id) is None:
    abort(404)

  delete_location(location_id, confirm=True)

  return redirect(url_for("admin.settings", tab=_LOCATION_TAB))


@admin.route("/custom-fields", methods=["POST"])
@login_required
@permission_required("custom_fields.manage")
def create_custom_field_route():
  name = request.form.get("name", "").strip()
  field_type = request.form.get("field_type", "")
  description = request.form.get("description", "").strip() or None
  required = request.form.get("required") == "true"
  enum_values = _parse_enum_values(request.form.get("enum_values"))

  try:
    create_custom_field(
      name=name,
      field_type=field_type,
      description=description,
      required=required,
      enum_values=enum_values,
    )
  except InvalidInputError as error:
    return _render_settings(
      _CUSTOM_FIELDS_TAB,
      error=str(error),
      field_name=name,
      field_type=field_type,
      field_description=request.form.get("description"),
      field_required=required,
      field_enum_values="\n".join(enum_values) if enum_values else "",
    )

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/custom-fields/<int:field_id>", methods=["POST"])
@login_required
@permission_required("custom_fields.manage")
def update_custom_field_route(field_id):
  name = request.form.get("name", "").strip()
  field_type = request.form.get("field_type")
  description = request.form.get("description")
  required = request.form.get("required") == "true"
  enum_values = _parse_enum_values(request.form.get("enum_values"))

  kwargs = {
    "name": name,
  }

  if field_type is not None:
    kwargs["field_type"] = field_type

  if description is not None:
    kwargs["description"] = description.strip() or None

  kwargs["required"] = required
  kwargs["enum_values"] = enum_values

  try:
    update_custom_field(field_id, **kwargs)
  except CustomFieldInUseError:
    return _render_settings(
      _CUSTOM_FIELDS_TAB,
      error="Cannot change the type of a field that already has values.",
    )
  except InvalidInputError as error:
    return _render_settings(
      _CUSTOM_FIELDS_TAB,
      error=str(error),
    )
  except CustomFieldNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/custom-fields/<int:field_id>/archive", methods=["POST"])
@login_required
@permission_required("custom_fields.manage")
def archive_custom_field_route(field_id):
  try:
    archive_custom_field(field_id)
  except CustomFieldNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/custom-fields/<int:field_id>/restore", methods=["POST"])
@login_required
@permission_required("custom_fields.manage")
def restore_custom_field_route(field_id):
  try:
    restore_custom_field(field_id)
  except CustomFieldNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/users", methods=["POST"])
@login_required
@permission_required("users.manage")
def create_user_route():
  # User management UI is not implemented yet; these routes stay registered
  # but are inert until then.
  return redirect(url_for("main.index"))


@admin.route("/users/<int:user_id>", methods=["POST"])
@login_required
@permission_required("users.manage")
def update_user_route(user_id):
  return redirect(url_for("main.index"))


@admin.route("/users/<int:user_id>/archive", methods=["POST"])
@login_required
@permission_required("users.manage")
def archive_user_route(user_id):
  return redirect(url_for("main.index"))


@admin.route("/users/<int:user_id>/restore", methods=["POST"])
@login_required
@permission_required("users.manage")
def restore_user_route(user_id):
  return redirect(url_for("main.index"))

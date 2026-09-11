from datetime import datetime

from flask import (
  Blueprint,
  abort,
  redirect,
  render_template,
  request,
  session,
  url_for,
)

import config

from ..services.auth.authentication import login_required
from ..services.auth.authorization import (
  check_permission,
  permission_required,
)
from ..services.data.audit import list_audit_logs
from ..services.data.custom_fields import (
  archive_custom_field,
  create_custom_field,
  get_custom_fields,
  restore_custom_field,
  update_custom_field,
)
from ..services.data.db import reset_database
from ..services.data.locations import (
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)
from ..services.data.users import get_users, verify_password
from ..services.exceptions.data.common import InvalidInputError
from ..services.exceptions.data.custom_fields import (
  CustomFieldInUseError,
  CustomFieldNotFoundError,
)
from ..services.exceptions.data.locations import (
  LocationAlreadyExistsError,
  LocationNotFoundError,
)

admin = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
)

_LOCATION_TAB = "locations"
_CUSTOM_FIELDS_TAB = "custom-fields"
_DATA_TAB = "data"
_VALID_TABS = (
  _LOCATION_TAB,
  _CUSTOM_FIELDS_TAB,
  _DATA_TAB,
)

_AUDIT_PAGE_SIZE = 50


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
    can_view_audit=check_permission(user_id, "audit.read"),
    debug=config.DEBUG,
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
    _DATA_TAB: (),
  }

  tab_permissions = permission_by_tab[active_tab]

  # Tabs with no required permissions (the data tab) stay login-gated only.
  if tab_permissions and not any(
    check_permission(session.get("user_id"), permission_name)
    for permission_name in tab_permissions
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


@admin.route("/data/reset", methods=["POST"])
@login_required
def reset_database_route():
  if not config.DEBUG:
    abort(404)

  password = request.form.get("password", "")
  confirm_password = request.form.get("confirm_password", "")

  if password != confirm_password:
    return _render_settings(
      _DATA_TAB,
      error="Passwords do not match.",
    )

  user_id = session.get("user_id")

  if not verify_password(user_id, password):
    return _render_settings(
      _DATA_TAB,
      error="Incorrect password.",
    )

  reset_database()
  session.clear()

  return redirect(url_for("auth.setup"))


def _parse_audit_filters():
  try:
    page = int(request.args.get("page", "1"))
  except ValueError:
    abort(400)

  if page < 1:
    abort(400)

  raw_user_id = request.args.get("user_id")

  if raw_user_id:
    try:
      user_id = int(raw_user_id)
    except ValueError:
      abort(400)
  else:
    user_id = None

  from_date = request.args.get("from")
  to_date = request.args.get("to")

  from_datetime = None
  to_datetime = None

  if from_date:
    try:
      from_datetime = datetime.strptime(from_date, "%Y-%m-%d")
    except ValueError:
      abort(400)

  if to_date:
    try:
      to_datetime = datetime.strptime(to_date, "%Y-%m-%d")
    except ValueError:
      abort(400)

  if from_datetime and to_datetime and from_datetime > to_datetime:
    abort(400)

  return {
    "entity_type": request.args.get("entity_type") or None,
    "entity_id": request.args.get("entity_id") or None,
    "action": request.args.get("action") or None,
    "user_id": user_id,
    "from_date": from_date or None,
    "to_date": to_date or None,
    "page": page,
  }


def _audit_query(filters):
  page = filters.pop("page")

  result = list_audit_logs(
    **filters,
    limit=_AUDIT_PAGE_SIZE,
    offset=(page - 1) * _AUDIT_PAGE_SIZE,
  )

  return result, page


def _audit_filter_chips(filters, users):
  """Build removable active-filter chips for the audit page toolbar.

  ``filters`` holds the 6 filter keys (user_id is an int) with None/empty
  for absent values. Each chip labels one active filter and links to the
  same listing without it.
  """
  query_names = {
    "entity_type": "entity_type",
    "action": "action",
    "user_id": "user_id",
    "entity_id": "entity_id",
    "from_date": "from",
    "to_date": "to",
  }

  definitions = (
    ("entity_type", "Type", "value"),
    ("action", "Action", "value"),
    ("user_id", "User", "username"),
    ("entity_id", "ID", "value"),
    ("from_date", "From", "value"),
    ("to_date", "To", "value"),
  )

  present = {
    key: value
    for key, value in filters.items()
    if value not in (None, "")
  }

  chips = []

  for key, prefix, kind in definitions:
    if key not in present:
      continue

    value = present[key]

    if kind == "username":
      value = next(
        (user["username"] for user in users if user["id"] == value),
        value,
      )

    remaining = {k: v for k, v in present.items() if k != key}

    chips.append(
      {
        "label": f"{prefix}: {value}",
        "remove_url": url_for(
          "admin.audit_route",
          **{query_names[k]: v for k, v in remaining.items()},
        ),
      }
    )

  return chips


@admin.route("/audit", methods=["GET"])
@login_required
@permission_required("audit.read")
def audit_route():
  parsed = _parse_audit_filters()
  result, page = _audit_query(parsed)

  total = result["total"]
  users = get_users()

  return render_template(
    "admin/audit.jinja",
    logs=result["logs"],
    total=total,
    page=page,
    has_more=page * _AUDIT_PAGE_SIZE < total,
    entity_types=result["entity_types"],
    actions=result["actions"],
    users=users,
    chips=_audit_filter_chips(parsed, users),
    filters={
      key: value
      for key, value in {
        "entity_type": request.args.get("entity_type") or "",
        "entity_id": request.args.get("entity_id") or "",
        "action": request.args.get("action") or "",
        "user_id": request.args.get("user_id") or "",
        "from": request.args.get("from") or "",
        "to": request.args.get("to") or "",
      }.items()
    },
  )


@admin.route("/audit/fragment", methods=["GET"])
@login_required
@permission_required("audit.read")
def audit_fragment_route():
  result, page = _audit_query(_parse_audit_filters())

  return render_template(
    "admin/audit_rows.jinja",
    logs=result["logs"],
    has_more=page * _AUDIT_PAGE_SIZE < result["total"],
    next_page=page + 1,
    filters={
      key: value
      for key, value in {
        "entity_type": request.args.get("entity_type") or "",
        "entity_id": request.args.get("entity_id") or "",
        "action": request.args.get("action") or "",
        "user_id": request.args.get("user_id") or "",
        "from": request.args.get("from") or "",
        "to": request.args.get("to") or "",
      }.items()
    },
  )

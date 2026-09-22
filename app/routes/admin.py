from datetime import date

from flask import (
  Blueprint,
  abort,
  jsonify,
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
  get_custom_field,
  get_custom_fields,
  restore_custom_field,
  update_custom_field,
)
from ..services.data.db import reset_database
from ..services.data.field_permissions import (
  get_field_role_permissions,
  set_field_role_permissions,
)
from ..services.data.locations import (
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)
from ..services.data.permissions import (
  create_permission,
  get_permission_by_name,
)
from ..services.data.role_permissions import (
  delete_role_permission,
  get_role_permissions,
  set_role_permission,
)
from ..services.data.roles import (
  create_role,
  delete_role,
  get_role,
  get_roles,
  update_role,
)
from ..services.data.user_permissions import (
  delete_user_permission,
  get_user_permissions,
  set_user_permission,
)
from ..services.data.user_roles import (
  delete_user_role,
  get_role_user_count,
  get_user_roles,
  is_admin_role,
  is_role_assigned,
  set_user_role,
)
from ..services.data.users import (
  archive_user,
  create_user,
  get_user,
  get_user_by_username,
  get_users,
  restore_archived_user,
  restore_user,
  update_user,
  verify_password,
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
from ..services.exceptions.data.permissions import (
  PermissionAlreadyExistsError,
  PermissionNotFoundError,
)
from ..services.exceptions.data.roles import (
  RoleAlreadyExistsError,
  RoleNotFoundError,
)
from ..services.exceptions.data.user_permissions import (
  UserPermissionNotFoundError,
)
from ..services.exceptions.data.users import (
  UserIsArchivedError,
  UserIsNotArchivedError,
  UsernameAlreadyExistsError,
  UsernameIsArchivedError,
  UserNotFoundError,
)

admin = Blueprint(
  "admin",
  __name__,
  url_prefix="/admin",
)

_LOCATION_TAB = "locations"
_CUSTOM_FIELDS_TAB = "custom-fields"
_DATA_TAB = "data"
_AUDIT_TAB = "audit"
_USERS_TAB = "users"
_ROLES_TAB = "roles"
_VALID_TABS = (
  _LOCATION_TAB,
  _CUSTOM_FIELDS_TAB,
  _DATA_TAB,
  _AUDIT_TAB,
  _USERS_TAB,
  _ROLES_TAB,
)

_AUDIT_PAGE_SIZE = 50


def _users_with_roles():
  return [{**user, "roles": get_user_roles(user["id"])} for user in get_users()]


def _roles_with_permissions(roles):
  return [
    {
      **role,
      "permissions": get_role_permissions(role["id"]),
      "user_count": get_role_user_count(role["id"]),
    }
    for role in roles
  ]


def _render_settings(
  active_tab,
  error=None,
  **context,
):
  user_id = session.get("user_id")
  can_view_audit = check_permission(user_id, "audit.read")
  can_manage_users = any(
    check_permission(user_id, permission_name)
    for permission_name in ("users.create", "users.update", "users.delete")
  )
  can_manage_roles = any(
    check_permission(user_id, permission_name)
    for permission_name in ("roles.create", "roles.update", "roles.delete")
  )

  all_roles = get_roles()

  audit_context = {}

  # The audit panel is rendered (hidden) for every permitted user so the
  # client-side tab switcher can reveal it without a page load.
  if can_view_audit:
    parsed = _parse_audit_filters()
    result, page = _audit_query(parsed)
    users = get_users()

    audit_context = {
      "logs": result["logs"],
      "total": result["total"],
      "page": page,
      "has_more": page * _AUDIT_PAGE_SIZE < result["total"],
      "entity_types": result["entity_types"],
      "actions": result["actions"],
      "users": users,
      "chips": _audit_filter_chips(parsed, users),
      "filters": _audit_view_filters(),
    }

  users_context = {}

  if can_manage_users:
    users_context = {
      "users_with_roles": _users_with_roles(),
    }

  roles_context = {}

  if can_manage_roles:
    roles_context = {
      "roles_with_permissions": _roles_with_permissions(all_roles),
    }

  render_context = {
    "locations": get_locations(),
    "custom_fields": get_custom_fields(),
    "archived_custom_fields": get_custom_fields(include_archived=True),
    "active_tab": active_tab,
    "error": error,
    "can_manage_locations": any(
      check_permission(user_id, permission_name)
      for permission_name in (
        "locations.create",
        "locations.update",
        "locations.delete",
      )
    ),
    "can_manage_custom_fields": any(
      check_permission(user_id, permission_name)
      for permission_name in ("field.create", "field.delete")
    ),
    "can_manage_backups": (
      check_permission(user_id, "backups.create")
      or check_permission(user_id, "backups.restore")
    ),
    "can_view_audit": can_view_audit,
    "can_manage_users": can_manage_users,
    "can_manage_roles": can_manage_roles,
    "debug": config.DEBUG,
    "backup_location": config.BACKUP_DIR,
    **audit_context,
    **users_context,
    **roles_context,
  }

  if can_manage_users or can_manage_roles:
    render_context["roles"] = [{"id": r["id"], "name": r["name"]} for r in all_roles]

  return render_template(
    "admin/settings.jinja",
    **render_context,
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
    _LOCATION_TAB: ("locations.create", "locations.update", "locations.delete"),
    _CUSTOM_FIELDS_TAB: ("field.create", "field.delete"),
    _DATA_TAB: (),
    _AUDIT_TAB: ("audit.read",),
    _USERS_TAB: ("users.create", "users.update", "users.delete"),
    _ROLES_TAB: ("roles.create", "roles.update", "roles.delete"),
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
@permission_required("locations.create")
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
@permission_required("locations.update")
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
@permission_required("locations.delete")
def delete_location_route(location_id):
  if get_location(location_id) is None:
    abort(404)

  delete_location(location_id, confirm=True)

  return redirect(url_for("admin.settings", tab=_LOCATION_TAB))


@admin.route("/custom-fields", methods=["POST"])
@login_required
@permission_required("field.create")
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
      copyable=request.form.get("copyable") == "true",
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
def update_custom_field_route(field_id):
  user_id = session.get("user_id")

  if not check_permission(user_id, f"field.{field_id}.update"):
    abort(403)

  name = request.form.get("name", "").strip()
  field_type = request.form.get("field_type")
  description = request.form.get("description")
  required = request.form.get("required") == "true"
  copyable = request.form.get("copyable") == "true"
  enum_values = _parse_enum_values(request.form.get("enum_values"))

  kwargs = {
    "name": name,
  }

  if field_type is not None:
    kwargs["field_type"] = field_type

  if description is not None:
    kwargs["description"] = description.strip() or None

  kwargs["required"] = required
  kwargs["copyable"] = copyable
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
@permission_required("field.delete")
def archive_custom_field_route(field_id):
  try:
    archive_custom_field(field_id)
  except CustomFieldNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/custom-fields/<int:field_id>/restore", methods=["POST"])
@login_required
@permission_required("field.create")
def restore_custom_field_route(field_id):
  try:
    restore_custom_field(field_id)
  except CustomFieldNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/custom-fields/<int:field_id>/permissions", methods=["GET"])
@login_required
def get_field_permissions_route(field_id):
  user_id = session.get("user_id")

  if not check_permission(user_id, f"field.{field_id}.read"):
    abort(403)

  if get_custom_field(field_id) is None:
    abort(404)

  roles = [role for role in get_roles() if not is_admin_role(role["id"])]

  return jsonify(
    {
      "roles": [
        {
          "id": role["id"],
          "name": role["name"],
        }
        for role in roles
      ],
      "permissions": get_field_role_permissions(field_id),
    }
  )


@admin.route("/custom-fields/<int:field_id>/permissions", methods=["POST"])
@login_required
def set_field_permissions_route(field_id):
  user_id = session.get("user_id")

  if not check_permission(user_id, f"field.{field_id}.update"):
    abort(403)

  if get_custom_field(field_id) is None:
    abort(404)

  read_role_ids = [
    int(raw) for raw in request.form.getlist("read_role_ids") if raw.strip().isdigit()
  ]
  update_role_ids = [
    int(raw) for raw in request.form.getlist("update_role_ids") if raw.strip().isdigit()
  ]

  set_field_role_permissions(
    field_id,
    read_role_ids,
    update_role_ids,
  )

  return redirect(url_for("admin.settings", tab=_CUSTOM_FIELDS_TAB))


@admin.route("/users", methods=["POST"])
@login_required
@permission_required("users.create")
def create_user_route():
  username = request.form.get("username", "").strip()
  name = request.form.get("name", "").strip() or None
  password = request.form.get("password", "")
  restore_archived = request.form.get("restore_archived") == "true"

  try:
    if restore_archived:
      archived = get_user_by_username(
        username,
        include_archived=True,
      )

      if archived is not None and archived["archived_at"] is not None:
        restore_archived_user(
          username,
          name=name,
          password=password,
        )
      else:
        create_user(
          username=username,
          password=password,
          name=name,
        )
    else:
      create_user(
        username=username,
        password=password,
        name=name,
      )
  except (InvalidInputError, UsernameAlreadyExistsError) as error:
    return _render_settings(
      _USERS_TAB,
      error=str(error),
      user_username=username,
      user_name=name or "",
      user_password=password,
    )
  except UsernameIsArchivedError:
    return _render_settings(
      _USERS_TAB,
      archived_username_conflict=username,
      user_username=username,
      user_name=name or "",
      user_password=password,
    )

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route("/users/<int:user_id>", methods=["POST"])
@login_required
@permission_required("users.update")
def update_user_route(user_id):
  if get_user(user_id) is None:
    abort(404)

  kwargs = {}

  if request.form.get("username") is not None:
    kwargs["username"] = request.form.get("username", "").strip()

  if request.form.get("name") is not None:
    kwargs["name"] = request.form.get("name", "").strip() or None

  password = request.form.get("password", "")

  if password:
    kwargs["password"] = password

  role_ids = [
    int(raw) for raw in request.form.getlist("role_ids") if raw.strip().isdigit()
  ]
  desired_role_ids = set(role_ids)
  current_role_ids = {row["role_id"] for row in get_user_roles(user_id)}

  try:
    if kwargs:
      update_user(user_id, **kwargs)

    for role_id in desired_role_ids - current_role_ids:
      set_user_role(user_id, role_id)

    for role_id in current_role_ids - desired_role_ids:
      delete_user_role(user_id, role_id)
  except (
    InvalidInputError,
    UserIsArchivedError,
    RoleNotFoundError,
  ) as error:
    return _render_settings(
      _USERS_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route("/users/<int:user_id>/archive", methods=["POST"])
@login_required
@permission_required("users.delete")
def archive_user_route(user_id):
  if user_id == session.get("user_id"):
    return _render_settings(
      _USERS_TAB,
      error="Cannot archive your own account",
    )

  if get_user(user_id) is None:
    abort(404)

  try:
    archive_user(user_id)
  except UserIsArchivedError as error:
    return _render_settings(
      _USERS_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route("/users/<int:user_id>/restore", methods=["POST"])
@login_required
@permission_required("users.create")
def restore_user_route(user_id):
  if get_user(user_id) is None:
    abort(404)

  try:
    restore_user(user_id)
  except UserIsNotArchivedError as error:
    return _render_settings(
      _USERS_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route("/users/<int:user_id>/permissions", methods=["GET"])
@login_required
@permission_required("users.read")
def list_user_permissions_route(user_id):
  if get_user(user_id) is None:
    abort(404)

  return jsonify([dict(row) for row in get_user_permissions(user_id)])


@admin.route("/users/<int:user_id>/permissions", methods=["POST"])
@login_required
@permission_required("users.update")
def grant_user_permission_route(user_id):
  if get_user(user_id) is None:
    abort(404)

  if user_id == session.get("user_id"):
    return _render_settings(
      _USERS_TAB,
      error="Cannot modify your own permissions",
    )

  permission_name = request.form.get("permission_name", "").strip()
  allowed = request.form.get("allowed") in ("1", "true", "on")

  if not permission_name:
    return _render_settings(
      _USERS_TAB,
      error="Permission name cannot be empty",
    )

  permission = get_permission_by_name(permission_name)

  if permission is None:
    try:
      permission_id = create_permission(permission_name)
    except (
      InvalidInputError,
      PermissionAlreadyExistsError,
    ) as error:
      return _render_settings(
        _USERS_TAB,
        error=str(error),
      )
  else:
    permission_id = permission["id"]

  try:
    set_user_permission(user_id, permission_id, allowed)
  except (
    UserNotFoundError,
    PermissionNotFoundError,
  ):
    abort(404)
  except InvalidInputError as error:
    return _render_settings(
      _USERS_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route(
  "/users/<int:user_id>/permissions/<int:permission_id>/delete",
  methods=["POST"],
)
@login_required
@permission_required("users.update")
def remove_user_permission_route(user_id, permission_id):
  if get_user(user_id) is None:
    abort(404)

  if user_id == session.get("user_id"):
    return _render_settings(
      _USERS_TAB,
      error="Cannot modify your own permissions",
    )

  try:
    delete_user_permission(user_id, permission_id)
  except UserPermissionNotFoundError:
    abort(404)

  return redirect(url_for("admin.settings", tab=_USERS_TAB))


@admin.route("/roles", methods=["POST"])
@login_required
@permission_required("roles.create")
def create_role_route():
  name = request.form.get("name", "").strip()
  description = request.form.get("description", "").strip() or None

  try:
    create_role(
      name=name,
      description=description,
    )
  except (
    InvalidInputError,
    RoleAlreadyExistsError,
  ) as error:
    return _render_settings(
      _ROLES_TAB,
      error=str(error),
      role_name=name,
      role_description=description or "",
    )

  return redirect(url_for("admin.settings", tab=_ROLES_TAB))


@admin.route("/roles/<int:role_id>", methods=["POST"])
@login_required
@permission_required("roles.update")
def update_role_route(role_id):
  if get_role(role_id) is None:
    abort(404)

  kwargs = {}

  if request.form.get("name") is not None:
    kwargs["name"] = request.form.get("name", "").strip()

  if request.form.get("description") is not None:
    kwargs["description"] = request.form.get("description", "").strip() or None

  try:
    update_role(role_id, **kwargs)
  except (
    InvalidInputError,
    RoleAlreadyExistsError,
  ) as error:
    return _render_settings(
      _ROLES_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_ROLES_TAB))


@admin.route("/roles/<int:role_id>/delete", methods=["POST"])
@login_required
@permission_required("roles.delete")
def delete_role_route(role_id):
  if get_role(role_id) is None:
    abort(404)

  if is_admin_role(role_id):
    return _render_settings(
      _ROLES_TAB,
      error="The Admin role cannot be deleted",
    )

  if is_role_assigned(role_id):
    return _render_settings(
      _ROLES_TAB,
      error="Cannot delete a role that is still assigned to a user",
    )

  delete_role(role_id)

  return redirect(url_for("admin.settings", tab=_ROLES_TAB))


@admin.route("/roles/<int:role_id>/permissions", methods=["GET"])
@login_required
@permission_required("roles.read")
def list_role_permissions_route(role_id):
  if get_role(role_id) is None:
    abort(404)

  return jsonify([dict(row) for row in get_role_permissions(role_id)])


@admin.route("/roles/<int:role_id>/permissions", methods=["POST"])
@login_required
@permission_required("roles.update")
def grant_role_permission_route(role_id):
  if get_role(role_id) is None:
    abort(404)

  permission_name = request.form.get("permission_name", "").strip()
  allowed = request.form.get("allowed") in ("1", "true", "on")

  if not permission_name:
    return _render_settings(
      _ROLES_TAB,
      error="Permission name cannot be empty",
    )

  permission = get_permission_by_name(permission_name)

  if permission is None:
    try:
      permission_id = create_permission(permission_name)
    except (
      InvalidInputError,
      PermissionAlreadyExistsError,
    ) as error:
      return _render_settings(
        _ROLES_TAB,
        error=str(error),
      )
  else:
    permission_id = permission["id"]

  try:
    set_role_permission(role_id, permission_id, allowed)
  except (
    InvalidInputError,
    RoleNotFoundError,
  ) as error:
    return _render_settings(
      _ROLES_TAB,
      error=str(error),
    )

  return redirect(url_for("admin.settings", tab=_ROLES_TAB))


@admin.route(
  "/roles/<int:role_id>/permissions/<int:permission_id>/delete",
  methods=["POST"],
)
@login_required
@permission_required("roles.update")
def remove_role_permission_route(role_id, permission_id):
  if get_role(role_id) is None:
    abort(404)

  try:
    delete_role_permission(role_id, permission_id)
  except (
    InvalidInputError,
    RoleNotFoundError,
  ):
    abort(404)

  return redirect(url_for("admin.settings", tab=_ROLES_TAB))


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

  from_day = None
  to_day = None

  if from_date:
    try:
      from_day = date.fromisoformat(from_date)
    except ValueError:
      abort(400)

  if to_date:
    try:
      to_day = date.fromisoformat(to_date)
    except ValueError:
      abort(400)

  if from_day and to_day and from_day > to_day:
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

  present = {key: value for key, value in filters.items() if value not in (None, "")}

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
          "admin.settings",
          tab=_AUDIT_TAB,
          **{query_names[k]: v for k, v in remaining.items()},
        ),
      }
    )

  return chips


def _audit_view_filters():
  return {
    "entity_type": request.args.get("entity_type") or "",
    "entity_id": request.args.get("entity_id") or "",
    "action": request.args.get("action") or "",
    "user_id": request.args.get("user_id") or "",
    "from": request.args.get("from") or "",
    "to": request.args.get("to") or "",
  }


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
    filters=_audit_view_filters(),
  )

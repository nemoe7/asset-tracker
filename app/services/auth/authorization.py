from functools import wraps

from flask import (
  abort,
  session,
)

from ..data.role_permissions import get_role_permissions
from ..data.user_permissions import get_user_permissions
from ..data.user_roles import get_user_roles
from ..data.users import get_user
from ..exceptions.auth.orization import PermissionDeniedError


def _get_permission_precedence(permission_name):
  parts = permission_name.split(".")
  precedence = [permission_name]

  for index in range(len(parts) - 1, 0, -1):
    precedence.append(".".join(parts[:index]) + ".*")

  precedence.append("*")

  return precedence


def _get_direct_decision(
  user_id,
  precedence,
):
  permissions = get_user_permissions(user_id)

  decisions = {
    permission["permission"]: bool(permission["allowed"]) for permission in permissions
  }

  for permission_name in precedence:
    if permission_name in decisions:
      return bool(decisions[permission_name])

  return None


def _get_role_decision(
  user_id,
  precedence,
):
  roles = get_user_roles(user_id)

  decisions = {}

  for role in roles:
    permissions = get_role_permissions(role["role_id"])

    for permission in permissions:
      permission_name = permission["permission"]

      if permission_name not in precedence:
        continue

      allowed = bool(permission["allowed"])

      if permission_name not in decisions:
        decisions[permission_name] = allowed
      elif not allowed:
        decisions[permission_name] = False

  for permission_name in precedence:
    if permission_name in decisions:
      return bool(decisions[permission_name])

  return None


def check_permission(user_id, permission_name):
  user = get_user(user_id)

  if user is None or user["archived_at"] is not None:
    return False

  precedence = _get_permission_precedence(
    permission_name,
  )

  direct_decision = _get_direct_decision(
    user_id,
    precedence,
  )

  if direct_decision is not None:
    return direct_decision

  role_decision = _get_role_decision(
    user_id,
    precedence,
  )

  if role_decision is not None:
    return role_decision

  return permission_name.endswith(".read")


def require_permission(user_id, permission_name):
  if not check_permission(user_id, permission_name):
    raise PermissionDeniedError()


def permission_required(permission_name):
  def decorator(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
      user_id = session.get("user_id")

      if user_id is None:
        abort(403)

      require_permission(
        user_id,
        permission_name,
      )

      return view(*args, **kwargs)

    return wrapped

  return decorator

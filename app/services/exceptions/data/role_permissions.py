from .common import InvalidInputError


class RolePermissionNotFoundError(InvalidInputError):
  default_message = "Role permission does not exist"


class InvalidRolePermissionAllowedError(InvalidInputError):
  default_message = "Role permission allowed value must be a boolean"

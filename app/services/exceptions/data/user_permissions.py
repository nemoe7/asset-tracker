from .common import InvalidInputError


class UserPermissionNotFoundError(InvalidInputError):
  default_message = "User permission does not exist"


class InvalidUserPermissionAllowedError(InvalidInputError):
  default_message = "User permission allowed value must be a boolean"

from .common import InvalidInputError


class UserRoleNotFoundError(InvalidInputError):
  default_message = "User role does not exist"

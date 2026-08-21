from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidRoleNameError(InvalidInputError):
  default_message = "Role name cannot be empty"


class RoleAlreadyExistsError(ServiceError):
  default_message = "Role already exists"


class RoleNotFoundError(ServiceError):
  default_message = "Role does not exist"

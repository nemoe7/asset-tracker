from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidPermissionNameError(InvalidInputError):
  default_message = "Permission name cannot be empty"


class PermissionAlreadyExistsError(ServiceError):
  default_message = "Permission already exists"


class PermissionNotFoundError(ServiceError):
  default_message = "Permission does not exist"

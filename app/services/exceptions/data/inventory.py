from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidItemNameError(InvalidInputError):
  default_message = "Asset name cannot be empty"


class ItemNotFoundError(ServiceError):
  default_message = "Asset does not exist"


class ItemIsArchivedError(ServiceError):
  default_message = "Asset is archived"


class ItemIsNotArchivedError(ServiceError):
  default_message = "Asset is already archived"

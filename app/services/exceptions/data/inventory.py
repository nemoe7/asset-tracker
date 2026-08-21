from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidItemNameError(InvalidInputError):
  default_message = "Item name cannot be empty"


class ItemNotFoundError(ServiceError):
  default_message = "Item does not exist"


class ItemIsArchivedError(ServiceError):
  default_message = "Item is archived"


class ItemIsNotArchivedError(ServiceError):
  default_message = "Item is already archived"

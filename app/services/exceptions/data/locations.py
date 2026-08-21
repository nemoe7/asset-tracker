from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidLocationNameError(InvalidInputError):
  default_message = "Location name cannot be empty"


class LocationAlreadyExistsError(ServiceError):
  default_message = "Location already exists"


class LocationNotFoundError(ServiceError):
  default_message = "Location does not exist"


class LocationDeletionConfirmationRequired(ServiceError):
  default_message = "Deleting a location requires confirmation"

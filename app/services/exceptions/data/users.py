from .common import (
  InvalidInputError,
  ServiceError,
)


class InvalidPasswordError(InvalidInputError):
  default_message = "Invalid password"


class InvalidUsernameError(InvalidInputError):
  default_message = "Invalid username"


class UsernameAlreadyExistsError(ServiceError):
  default_message = "Username already exists"


class UsernameIsArchivedError(ServiceError):
  default_message = "Username is archived"


class UserNotFoundError(ServiceError):
  default_message = "User does not exist"


class UserIsArchivedError(ServiceError):
  default_message = "User is archived"


class UserIsNotArchivedError(ServiceError):
  default_message = "User is active"

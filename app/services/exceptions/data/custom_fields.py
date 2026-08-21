from .common import InvalidInputError


class InvalidCustomFieldNameError(InvalidInputError):
  default_message = "Custom field name cannot be empty"


class InvalidCustomFieldTypeError(InvalidInputError):
  default_message = "Invalid custom field type"


class InvalidCustomFieldRequiredError(InvalidInputError):
  default_message = "Required must be a boolean"


class InvalidCustomFieldEnumValuesError(InvalidInputError):
  default_message = "Invalid enum values"


class CustomFieldAlreadyExistsError(InvalidInputError):
  default_message = "Custom field already exists"


class CustomFieldNotFoundError(InvalidInputError):
  default_message = "Custom field does not exist"


class CustomFieldInUseError(InvalidInputError):
  default_message = "Custom field is in use"


class CustomFieldIsArchivedError(InvalidInputError):
  default_message = "Custom field is archived"

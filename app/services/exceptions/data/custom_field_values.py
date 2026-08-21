from .common import InvalidInputError


class InvalidCustomFieldValueError(InvalidInputError):
  default_message = "Invalid custom field value"


class CustomFieldValueNotFoundError(InvalidInputError):
  default_message = "Custom field value does not exist"


class InvalidCustomFieldEnumValueError(InvalidCustomFieldValueError):
  default_message = "Invalid enum value"


class RequiredCustomFieldError(InvalidCustomFieldValueError):
  default_message = "Required custom field cannot be unset"

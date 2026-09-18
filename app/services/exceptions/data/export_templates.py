from .common import InvalidInputError


class InvalidExportTemplateNameError(InvalidInputError):
  default_message = "Export template name cannot be empty"


class InvalidExportTemplateConfigurationError(InvalidInputError):
  default_message = "Invalid export template configuration"


class ExportTemplateNotFoundError(InvalidInputError):
  default_message = "Export template does not exist"


class ExportTemplateAccessError(InvalidInputError):
  default_message = "Not allowed to modify this export template"

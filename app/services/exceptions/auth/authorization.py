from ..data.common import ServiceError


class PermissionDeniedError(ServiceError):
  default_message = "Permission denied"

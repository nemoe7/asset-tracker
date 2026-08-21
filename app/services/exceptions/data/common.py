class ServiceError(Exception):
  default_message = "Service error"

  def __init__(self, message=None):
    super().__init__(self.default_message if message is None else message)


class InvalidInputError(ServiceError):
  default_message = "Invalid input"

from .common import ServiceError


class BackupError(ServiceError):
  default_message = "Backup failed"


class InvalidBackupError(BackupError):
  default_message = "Not a valid backup file"

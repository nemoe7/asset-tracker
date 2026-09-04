import logging

from flask import (
  Blueprint,
  Response,
  jsonify,
  request,
  session,
)

from ..services.auth.authentication import login_required
from ..services.auth.authorization import permission_required
from ..services.data.backups import create_backup, restore_backup
from ..services.data.users import verify_password
from ..services.exceptions.data.backups import (
  BackupError,
  InvalidBackupError,
)

logger = logging.getLogger(__name__)

backups = Blueprint(
  "backups",
  __name__,
  url_prefix="/backups",
)


@backups.route("/create", methods=["POST"])
@login_required
@permission_required("backups.create")
def create():
  try:
    result = create_backup(session["user_id"])
  except BackupError:
    logger.exception("Backup creation failed")

    return jsonify({"error": "Backup failed"}), 500

  return Response(
    result["data"],
    mimetype="application/x-sqlite3",
    headers={
      "Content-Disposition": f'attachment; filename="{result["filename"]}"',
    },
  )


@backups.route("/restore", methods=["POST"])
@login_required
@permission_required("backups.restore")
def restore():
  password = request.form.get("password")
  file = request.files.get("file")

  if not password or file is None:
    return jsonify({"error": "Backup file and password are required"}), 400

  # Verified before any destructive action is taken (BKP-013).
  if not verify_password(session["user_id"], password):
    return jsonify({"error": "Incorrect password"}), 400

  try:
    restore_backup(file)
  except InvalidBackupError as error:
    return jsonify({"error": str(error)}), 400
  except BackupError:
    logger.exception("Backup restore failed")

    return jsonify({"error": "Restore failed"}), 500

  return jsonify({"status": "ok"})

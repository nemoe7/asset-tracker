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
from ..services.data.backups import create_backup
from ..services.exceptions.data.backups import BackupError

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
  return jsonify({"status": "ok"})

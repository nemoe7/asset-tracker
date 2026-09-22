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
from ..services.data.audit import create_audit_log
from ..services.data.backups import (
  create_backup,
  get_backup_config,
  restore_backup,
  update_backup_config,
)
from ..services.data.users import verify_password
from ..services.exceptions.data.backups import (
  BackupError,
  InvalidBackupError,
)
from ..services.exceptions.data.common import InvalidInputError
from ..services.executor import run_backup_job

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


@backups.route("/config", methods=["GET"])
@login_required
@permission_required("backups.create")
def get_config():
  return jsonify(get_backup_config())


@backups.route("/config", methods=["PUT"])
@login_required
@permission_required("backups.create")
def update_config():
  payload = request.get_json(silent=True)
  if not isinstance(payload, dict):
    return jsonify({"error": "JSON body required"}), 400

  enabled = payload.get("enabled")
  schedule = payload.get("schedule")
  if enabled is None and schedule is None:
    return jsonify({"error": "enabled or schedule required"}), 400

  try:
    config = update_backup_config(enabled=enabled, schedule=schedule)
  except InvalidInputError as error:
    return jsonify({"error": str(error)}), 400

  create_audit_log(
    action="updated",
    entity_type="backup_config",
    entity_id="backup",
    details={"enabled": config["enabled"], "schedule": config["schedule"]},
  )

  return jsonify(config)


@backups.route("/run-now", methods=["POST"])
@login_required
@permission_required("backups.create")
def run_now():
  try:
    result = run_backup_job(user_id=session["user_id"])
  except BackupError:
    logger.exception("Manual backup run failed")

    return jsonify({"error": "Backup failed"}), 500

  return jsonify(
    {
      "filename": result["filename"],
      "path": result["path"],
      "scheduled_at": result["scheduled_at"],
      "completed_at": result["completed_at"],
    }
  )

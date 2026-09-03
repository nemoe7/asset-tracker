import json

from ..auth.context import get_current_user
from .db import db_connection, db_transaction


def create_audit_log(
  action,
  entity_type,
  entity_id,
  details=None,
):
  user_id = get_current_user()

  if user_id is None:
    raise RuntimeError("No current user")

  with db_transaction() as connection:
    result = connection.execute(
      """
      INSERT INTO audit_log (
        user_id,
        action,
        entity_type,
        entity_id,
        details,
        timestamp
      )
      VALUES (?, ?, ?, ?, ?, datetime('now'))
      """,
      (
        user_id,
        action,
        entity_type,
        str(entity_id),
        json.dumps(details) if details is not None else None,
      ),
    )

    return result.lastrowid


def _parse_audit_log(row):
  if row is None:
    return None

  row = dict(row)

  if row["details"] is not None:
    row["details"] = json.loads(row["details"])

  return row


def get_audit_log(audit_id):
  with db_connection() as connection:
    row = connection.execute(
      """
      SELECT *
      FROM audit_log
      WHERE id = ?
      """,
      (audit_id,),
    ).fetchone()

    return _parse_audit_log(row)


def get_audit_logs(entity_type=None, entity_id=None):
  with db_connection() as connection:
    query = """
      SELECT *
      FROM audit_log
      WHERE 1 = 1
    """

    parameters = []

    if entity_type is not None:
      query += " AND entity_type = ?"
      parameters.append(entity_type)

    if entity_id is not None:
      query += " AND entity_id = ?"
      parameters.append(str(entity_id))

    query += " ORDER BY id"

    rows = connection.execute(
      query,
      parameters,
    ).fetchall()

    return [_parse_audit_log(row) for row in rows]

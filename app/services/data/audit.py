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
    try:
      row["details"] = json.loads(row["details"])
    except json.JSONDecodeError:
      # A corrupt stored value degrades to the raw string instead of a 500.
      pass

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


def list_audit_logs(
  entity_type=None,
  entity_id=None,
  action=None,
  user_id=None,
  from_date=None,
  to_date=None,
  limit=50,
  offset=0,
):
  """Filtered, newest-first audit listing for the activity log page.

  Returns the page of logs, the total matching count (before
  limit/offset), and the distinct entity types/actions for the filter
  dropdowns. ``from_date``/``to_date`` are inclusive 'YYYY-MM-DD' strings
  compared against the UTC 'YYYY-MM-DD HH:MM:SS' timestamps.
  """
  with db_connection() as connection:
    where_clauses = []
    parameters = []

    if entity_type is not None:
      where_clauses.append("audit_log.entity_type = ?")
      parameters.append(entity_type)

    if entity_id is not None:
      where_clauses.append("audit_log.entity_id = ?")
      parameters.append(str(entity_id))

    if action is not None:
      where_clauses.append("audit_log.action = ?")
      parameters.append(action)

    if user_id is not None:
      where_clauses.append("audit_log.user_id = ?")
      parameters.append(user_id)

    if from_date is not None:
      where_clauses.append("audit_log.timestamp >= ?")
      parameters.append(f"{from_date} 00:00:00")

    if to_date is not None:
      where_clauses.append("audit_log.timestamp <= ?")
      parameters.append(f"{to_date} 23:59:59")

    where_sql = ""

    if where_clauses:
      where_sql = "WHERE " + " AND ".join(where_clauses)

    total = connection.execute(
      f"""
      SELECT COUNT(*)
      FROM audit_log
      {where_sql}
      """,
      parameters,
    ).fetchone()[0]

    rows = connection.execute(
      f"""
      SELECT
        audit_log.*,
        users.username AS username
      FROM audit_log
      INNER JOIN users ON users.id = audit_log.user_id
      {where_sql}
      ORDER BY audit_log.id DESC
      LIMIT ? OFFSET ?
      """,
      [*parameters, limit, offset],
    ).fetchall()

    entity_types = [
      row["entity_type"]
      for row in connection.execute(
        "SELECT DISTINCT entity_type FROM audit_log ORDER BY entity_type"
      ).fetchall()
    ]

    actions = [
      row["action"]
      for row in connection.execute(
        "SELECT DISTINCT action FROM audit_log ORDER BY action"
      ).fetchall()
    ]

    return {
      "logs": [_parse_audit_log(row) for row in rows],
      "total": total,
      "entity_types": entity_types,
      "actions": actions,
    }

import json

from app.db import get_db


def create_audit_log(
  action,
  entity_type,
  entity_id,
  user_id=None,
  details=None,
  connection=None,
):
  owns_connection = connection is None

  if owns_connection:
    connection = get_db()

  try:
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

    if owns_connection:
      connection.commit()

    return result.lastrowid
  finally:
    if owns_connection:
      connection.close()


def get_audit_log(audit_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM audit_log
      WHERE id = ?
      """,
      (audit_id,),
    ).fetchone()
  finally:
    connection.close()


def get_audit_logs(entity_type=None, entity_id=None):
  connection = get_db()

  try:
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

    return connection.execute(
      query,
      parameters,
    ).fetchall()
  finally:
    connection.close()

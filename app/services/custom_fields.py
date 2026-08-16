from app.db import get_db
from app.services.audit import create_audit_log

_UNSET = object()

VALID_FIELD_TYPES = {
  "text",
  "integer",
  "decimal",
  "boolean",
  "date",
}


def create_custom_field(
  name,
  field_type,
  description=None,
):
  if not name:
    raise ValueError("Custom field name cannot be empty")

  if field_type not in VALID_FIELD_TYPES:
    raise ValueError("Invalid custom field type")

  connection = get_db()

  try:
    result = connection.execute(
      """
      INSERT INTO custom_fields (
        name,
        field_type,
        description
      )
      VALUES (?, ?, ?)
      """,
      (
        name,
        field_type,
        description,
      ),
    )

    field_id = result.lastrowid

    create_audit_log(
      action="created",
      entity_type="custom_field",
      entity_id=field_id,
      connection=connection,
    )

    connection.commit()

    return field_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_custom_field(field_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()
  finally:
    connection.close()


def get_custom_fields():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM custom_fields
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_custom_field(
  field_id,
  name=None,
  field_type=None,
  description=_UNSET,
):
  if name is not None and not name:
    raise ValueError("Custom field name cannot be empty")

  if field_type is not None and field_type not in VALID_FIELD_TYPES:
    raise ValueError("Invalid custom field type")

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT *
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if existing is None:
      return False

    new_name = existing["name"] if name is None else name

    new_field_type = existing["field_type"] if field_type is None else field_type

    new_description = existing["description"] if description is _UNSET else description

    details = {}

    if existing["name"] != new_name:
      details["name"] = {
        "old": existing["name"],
        "new": new_name,
      }

    if existing["field_type"] != new_field_type:
      details["field_type"] = {
        "old": existing["field_type"],
        "new": new_field_type,
      }

    if existing["description"] != new_description:
      details["description"] = {
        "old": existing["description"],
        "new": new_description,
      }

    if not details:
      return True

    connection.execute(
      """
      UPDATE custom_fields
      SET name = ?,
          field_type = ?,
          description = ?
      WHERE id = ?
      """,
      (
        new_name,
        new_field_type,
        new_description,
        field_id,
      ),
    )

    create_audit_log(
      action="updated",
      entity_type="custom_field",
      entity_id=field_id,
      details=details,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

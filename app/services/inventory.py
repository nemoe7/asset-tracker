import uuid

from app.db import get_db
from app.services.audit import create_audit_log


def create_item(name, location_id=None):
  item_id = str(uuid.uuid4())

  connection = get_db()

  try:
    connection.execute(
      """
      INSERT INTO inventory_items (
        id,
        name,
        location_id,
        created_at,
        updated_at
      )
      VALUES (?, ?, ?, datetime('now'), datetime('now'))
      """,
      (item_id, name, location_id),
    )

    create_audit_log(
      action="created",
      entity_type="inventory_item",
      entity_id=item_id,
      connection=connection,
    )

    connection.commit()

    return item_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_item(item_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()
  finally:
    connection.close()


def get_items():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM inventory_items
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_item(item_id, name, location_id=None):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT name, location_id
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()

    if existing is None:
      return False

    details = {}

    if existing["name"] != name:
      details["name"] = {
        "old": existing["name"],
        "new": name,
      }

    if existing["location_id"] != location_id:
      details["location_id"] = {
        "old": existing["location_id"],
        "new": location_id,
      }

    if not details:
      return True

    connection.execute(
      """
      UPDATE inventory_items
      SET name = ?,
          location_id = ?,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (name, location_id, item_id),
    )

    create_audit_log(
      action="updated",
      entity_type="inventory_item",
      entity_id=item_id,
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


def delete_item(item_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      DELETE FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    )

    if result.rowcount == 0:
      return False

    create_audit_log(
      action="deleted",
      entity_type="inventory_item",
      entity_id=item_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

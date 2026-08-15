import uuid

from app.db import get_db


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

    connection.commit()

    return item_id
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
    result = connection.execute(
      """
      UPDATE inventory_items
      SET name = ?,
          location_id = ?,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (name, location_id, item_id),
    )

    connection.commit()

    return result.rowcount > 0
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

    connection.commit()

    return result.rowcount > 0
  finally:
    connection.close()

from app.db import get_db


class LocationInUseError(Exception):
  pass


def create_location(name, description=None):
  connection = get_db()

  try:
    result = connection.execute(
      """
      INSERT INTO locations (
        name,
        description,
        created_at,
        updated_at
      )
      VALUES (?, ?, datetime('now'), datetime('now'))
      """,
      (name, description),
    )

    connection.commit()

    return result.lastrowid
  finally:
    connection.close()


def get_location(location_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()
  finally:
    connection.close()


def get_locations():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM locations
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_location(location_id, name, description=None):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE locations
      SET name = ?,
          description = ?,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (name, description, location_id),
    )

    connection.commit()

    return result.rowcount > 0
  finally:
    connection.close()


def delete_location(location_id):
  connection = get_db()

  try:
    location = connection.execute(
      """
      SELECT id
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()

    if location is None:
      return False

    item = connection.execute(
      """
      SELECT 1
      FROM inventory_items
      WHERE location_id = ?
      LIMIT 1
      """,
      (location_id,),
    ).fetchone()

    if item is not None:
      raise LocationInUseError("Cannot delete a location that contains inventory items")

    connection.execute(
      """
      DELETE FROM locations
      WHERE id = ?
      """,
      (location_id,),
    )

    connection.commit()

    return True
  finally:
    connection.close()

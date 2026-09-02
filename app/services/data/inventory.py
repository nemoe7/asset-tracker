import uuid
from decimal import Decimal

from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.inventory import *
from ..exceptions.data.locations import LocationNotFoundError
from .audit import create_audit_log
from .db import db_connection, db_transaction
from .locations import get_location

_UNSET = object()


def _validate_item_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidItemNameError()


def _validate_location(location_id):
  if location_id is None:
    return

  if get_location(location_id) is None:
    raise LocationNotFoundError()


def _get_custom_fields(connection, item_id):
  rows = connection.execute(
    """
    SELECT
      inventory_item_fields.value,
      custom_fields.name,
      custom_fields.field_type
    FROM inventory_item_fields
    JOIN custom_fields
      ON custom_fields.id = inventory_item_fields.field_id
    WHERE inventory_item_fields.item_id = ?
    """,
    (item_id,),
  ).fetchall()

  fields = {}

  for row in rows:
    value = row["value"]
    field_type = row["field_type"]

    if field_type == "integer":
      value = int(value)
    elif field_type == "decimal":
      value = Decimal(value)
    elif field_type == "boolean":
      value = value == "1"

    fields[row["name"]] = value

  return fields


def _item_with_custom_fields(connection, item):
  if item is None:
    return None

  item = dict(item)
  item["custom_fields"] = _get_custom_fields(
    connection,
    item["id"],
  )

  return item


def _build_item_query(
  connection,
  search,
  location_id,
  include_archived,
  custom_fields,
  sort_by,
  sort_order,
):
  if sort_order not in ("asc", "desc"):
    raise InvalidInputError("Invalid sort order")

  conditions = []
  parameters = []

  if not include_archived:
    conditions.append("inventory_items.archived_at IS NULL")

  if search:
    conditions.append("inventory_items.name LIKE ?")
    parameters.append(f"%{search}%")

  if location_id is not _UNSET:
    if location_id is None:
      conditions.append("inventory_items.location_id IS NULL")
    else:
      _validate_location(location_id)

      conditions.append("inventory_items.location_id = ?")
      parameters.append(location_id)

  if custom_fields:
    for field_id, value in custom_fields.items():
      conditions.append(
        """
        EXISTS (
          SELECT 1
          FROM inventory_item_fields
          WHERE inventory_item_fields.item_id = inventory_items.id
            AND inventory_item_fields.field_id = ?
            AND inventory_item_fields.value = ?
        )
        """
      )
      parameters.extend(
        [
          field_id,
          str(value),
        ]
      )

  where_clause = ""

  if conditions:
    where_clause = f"WHERE {' AND '.join(conditions)}"

  if sort_by == "name":
    sort_expression = "inventory_items.name"
    sort_join = ""
    sort_parameters = []
    null_order = ""

  else:
    field = connection.execute(
      """
      SELECT
        id,
        field_type
      FROM custom_fields
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (sort_by,),
    ).fetchone()

    if field is None:
      raise InvalidInputError("Invalid sort field")

    if field["field_type"] in (
      "integer",
      "decimal",
      "user",
    ):
      sort_expression = "CAST(inventory_item_fields.value AS NUMERIC)"
    elif field["field_type"] == "boolean":
      sort_expression = "CAST(inventory_item_fields.value AS INTEGER)"
    else:
      sort_expression = "inventory_item_fields.value"

    sort_join = """
      LEFT JOIN inventory_item_fields
        ON inventory_item_fields.item_id = inventory_items.id
        AND inventory_item_fields.field_id = ?
    """

    sort_parameters = [sort_by]

    null_order = "CASE WHEN inventory_item_fields.value IS NULL THEN 0 ELSE 1 END,"

  from_clause = f"""
    FROM inventory_items
    LEFT JOIN locations
      ON locations.id = inventory_items.location_id
    {sort_join}
  """

  order_clause = f"""
    ORDER BY
      {null_order}
      {sort_expression} {sort_order.upper()},
      inventory_items.id
  """

  return (
    from_clause,
    where_clause,
    order_clause,
    [
      *sort_parameters,
      *parameters,
    ],
  )


def create_item(name, description=None, location_id=None):
  _validate_item_name(name)
  _validate_location(location_id)
  item_id = str(uuid.uuid4())

  with db_transaction() as connection:
    connection.execute(
      """
      INSERT INTO inventory_items (
        id,
        name,
        description,
        location_id,
        created_at,
        updated_at
      )
      VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))
      """,
      (
        item_id,
        name,
        description,
        location_id,
      ),
    )

    create_audit_log(
      action="created",
      entity_type="inventory_item",
      entity_id=item_id,
    )

    return item_id


def get_item(item_id, include_archived=False):
  with db_connection() as connection:
    archived_condition = ""

    if not include_archived:
      archived_condition = "AND inventory_items.archived_at IS NULL"

    item = connection.execute(
      f"""
      SELECT
        inventory_items.*,
        locations.name AS location_name
      FROM inventory_items
      LEFT JOIN locations
        ON locations.id = inventory_items.location_id
      WHERE inventory_items.id = ?
        {archived_condition}
      """,
      (item_id,),
    ).fetchone()

    return _item_with_custom_fields(
      connection,
      item,
    )


def get_items(
  search=None,
  location_id=None,
  include_archived=False,
  custom_fields=None,
  sort_by="name",
  sort_order="asc",
):
  with db_connection() as connection:
    (
      from_clause,
      where_clause,
      order_clause,
      parameters,
    ) = _build_item_query(
      connection,
      search,
      location_id,
      include_archived,
      custom_fields,
      sort_by,
      sort_order,
    )

    items = connection.execute(
      f"""
      SELECT
        inventory_items.*,
        locations.name AS location_name
      {from_clause}
      {where_clause}
      {order_clause}
      """,
      parameters,
    ).fetchall()

    return [
      _item_with_custom_fields(
        connection,
        item,
      )
      for item in items
    ]


def get_items_paginated(
  search=None,
  location_id=_UNSET,
  include_archived=False,
  custom_fields=None,
  sort_by="name",
  sort_order="asc",
  page=1,
  per_page=25,
):
  if page < 1:
    raise InvalidInputError("Invalid page")

  if per_page < 1:
    raise InvalidInputError("Invalid per_page")

  with db_connection() as connection:
    (
      from_clause,
      where_clause,
      order_clause,
      parameters,
    ) = _build_item_query(
      connection,
      search,
      location_id,
      include_archived,
      custom_fields,
      sort_by,
      sort_order,
    )

    total = connection.execute(
      f"""
      SELECT COUNT(*)
      {from_clause}
      {where_clause}
      """,
      parameters,
    ).fetchone()[0]

    total_pages = max(
      1,
      (total + per_page - 1) // per_page,
    )

    page = min(page, total_pages)

    offset = (page - 1) * per_page

    items = connection.execute(
      f"""
      SELECT
        inventory_items.*,
        locations.name AS location_name
      {from_clause}
      {where_clause}
      {order_clause}
      LIMIT ? OFFSET ?
      """,
      [
        *parameters,
        per_page,
        offset,
      ],
    ).fetchall()

    return {
      "items": [
        _item_with_custom_fields(
          connection,
          item,
        )
        for item in items
      ],
      "page": page,
      "per_page": per_page,
      "total": total,
      "total_pages": total_pages,
    }


def update_item(
  item_id,
  name=_UNSET,
  description=_UNSET,
  location_id=_UNSET,
):
  if name is _UNSET and description is _UNSET and location_id is _UNSET:
    raise InvalidInputError("No fields to update")

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()

    if existing is None:
      raise ItemNotFoundError()

    if existing["archived_at"] is not None:
      raise ItemIsArchivedError()

    updates = []
    values = []
    details = {}

    if name is not _UNSET:
      _validate_item_name(name)

      if existing["name"] != name:
        updates.append("name = ?")
        values.append(name)

        details["name"] = {
          "old": existing["name"],
          "new": name,
        }

    if description is not _UNSET and existing["description"] != description:
      updates.append("description = ?")
      values.append(description)

      details["description"] = {
        "old": existing["description"],
        "new": description,
      }

    if location_id is not _UNSET:
      _validate_location(location_id)

      if existing["location_id"] != location_id:
        updates.append("location_id = ?")
        values.append(location_id)

        details["location_id"] = {
          "old": existing["location_id"],
          "new": location_id,
        }

    if not updates:
      return True

    updates.append("updated_at = datetime('now')")
    values.append(item_id)

    connection.execute(
      f"""
      UPDATE inventory_items
      SET {", ".join(updates)}
      WHERE id = ?
        AND archived_at IS NULL
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="inventory_item",
      entity_id=item_id,
      details=details,
    )

    return True


def archive_item(item_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT archived_at
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()

    if existing is None:
      raise ItemNotFoundError()

    if existing["archived_at"] is not None:
      raise ItemIsArchivedError()

    connection.execute(
      """
      UPDATE inventory_items
      SET archived_at = datetime('now'),
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (item_id,),
    )

    create_audit_log(
      action="archived",
      entity_type="inventory_item",
      entity_id=item_id,
    )

    return True


def restore_item(item_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT archived_at
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()

    if existing is None:
      raise ItemNotFoundError()

    if existing["archived_at"] is None:
      raise ItemIsNotArchivedError()

    connection.execute(
      """
      UPDATE inventory_items
      SET archived_at = NULL,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (item_id,),
    )

    create_audit_log(
      action="restored",
      entity_type="inventory_item",
      entity_id=item_id,
    )

    return True

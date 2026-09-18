import json

from ..constants import UNSET
from ..exceptions.data.export_templates import (
  ExportTemplateAccessError,
  ExportTemplateNotFoundError,
  InvalidExportTemplateConfigurationError,
  InvalidExportTemplateNameError,
)
from .audit import create_audit_log
from .db import db_connection, db_transaction

_TEMPLATE_KEYS = ("filters", "columns")


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidExportTemplateNameError()


def _validate_configuration(configuration):
  if not isinstance(configuration, dict):
    raise InvalidExportTemplateConfigurationError()

  unknown = set(configuration) - set(_TEMPLATE_KEYS)
  if unknown:
    raise InvalidExportTemplateConfigurationError(
      f"Unknown configuration keys: {', '.join(sorted(unknown))}"
    )

  filters = configuration.get("filters")
  if filters is not None:
    if not isinstance(filters, list):
      raise InvalidExportTemplateConfigurationError()
    for row in filters:
      if (
        not isinstance(row, list)
        or len(row) != 3
        or any(not isinstance(value, str) for value in row)
      ):
        raise InvalidExportTemplateConfigurationError()

  columns = configuration.get("columns")
  if columns is not None and (
    not isinstance(columns, list)
    or not columns
    or any(not isinstance(value, str) or not value.strip() for value in columns)
    or len(columns) != len(set(columns))
  ):
    raise InvalidExportTemplateConfigurationError()


def _row_to_template(row):
  template = dict(row)
  template["configuration"] = json.loads(template["configuration"])
  template["shared"] = template["user_id"] is None
  template["owner_id"] = template.pop("user_id")
  return template


def create_export_template(user_id, name, configuration, shared=False):
  _validate_name(name)
  _validate_configuration(configuration)

  stored_user_id = None if shared else user_id

  with db_transaction() as connection:
    cursor = connection.execute(
      """
      INSERT INTO export_templates (user_id, name, configuration, created_at, updated_at)
      VALUES (?, ?, ?, datetime('now'), datetime('now'))
      """,
      (
        stored_user_id,
        name.strip(),
        json.dumps(configuration),
      ),
    )
    template_id = cursor.lastrowid

  create_audit_log(
    action="created",
    entity_type="export_template",
    entity_id=template_id,
    details={"name": name.strip(), "shared": shared},
  )

  return template_id


def _get_owned_row(connection, template_id):
  row = connection.execute(
    """
    SELECT id, user_id, name FROM export_templates WHERE id = ?
    """,
    (template_id,),
  ).fetchone()

  if row is None:
    raise ExportTemplateNotFoundError()

  return row


def get_export_template(template_id, user_id):
  with db_connection() as connection:
    row = connection.execute(
      """
      SELECT id, user_id, name, configuration, created_at, updated_at
      FROM export_templates
      WHERE id = ?
        AND (user_id = ? OR user_id IS NULL)
      """,
      (template_id, user_id),
    ).fetchone()

  if row is None:
    raise ExportTemplateNotFoundError()

  return _row_to_template(row)


def get_export_templates(user_id):
  with db_connection() as connection:
    rows = connection.execute(
      """
      SELECT id, user_id, name, configuration, created_at, updated_at
      FROM export_templates
      WHERE user_id = ? OR user_id IS NULL
      ORDER BY name
      """,
      (user_id,),
    ).fetchall()

  return [_row_to_template(row) for row in rows]


def update_export_template(
  template_id,
  user_id,
  name=UNSET,
  configuration=UNSET,
  allow_shared=False,
):
  if name is UNSET and configuration is UNSET:
    raise InvalidExportTemplateConfigurationError("No fields to update")

  if name is not UNSET:
    _validate_name(name)

  if configuration is not UNSET:
    _validate_configuration(configuration)

  with db_transaction() as connection:
    row = _get_owned_row(connection, template_id)

    if row["user_id"] is None:
      # Shared templates: visible to everyone, managed by admins only.
      # The route layer passes is_admin; the data layer only accepts
      # admin updates via the allow_shared flag.
      if not allow_shared:
        raise ExportTemplateAccessError()
    elif row["user_id"] != user_id:
      raise ExportTemplateNotFoundError()

    updates = []
    values = []

    if name is not UNSET:
      updates.append("name = ?")
      values.append(name.strip())

    if configuration is not UNSET:
      updates.append("configuration = ?")
      values.append(json.dumps(configuration))

    values.append(template_id)
    connection.execute(
      f"""
      UPDATE export_templates
      SET {", ".join(updates)}, updated_at = datetime('now')
      WHERE id = ?
      """,
      values,
    )

  create_audit_log(
    action="updated",
    entity_type="export_template",
    entity_id=template_id,
    details={"name": name.strip()} if name is not UNSET else None,
  )

  return get_export_template(template_id, user_id)


def delete_export_template(template_id, user_id, allow_shared=False):
  with db_transaction() as connection:
    row = _get_owned_row(connection, template_id)

    if row["user_id"] is None:
      if not allow_shared:
        raise ExportTemplateAccessError()
    elif row["user_id"] != user_id:
      raise ExportTemplateNotFoundError()

    connection.execute(
      """
      DELETE FROM export_templates WHERE id = ?
      """,
      (template_id,),
    )

  create_audit_log(
    action="deleted",
    entity_type="export_template",
    entity_id=template_id,
    details={"name": row["name"]},
  )

from .data.export_templates import get_export_template


def apply_export_template(template_id, user_id):
  """Return the query-string params to build /inventory/export from a saved template.

  Field visibility and column validity are enforced downstream by
  build_export's existing validation and visible_field_ids filtering.
  """
  template = get_export_template(template_id, user_id)
  configuration = template["configuration"]

  params = {}

  filters = configuration.get("filters") or []
  if filters:
    params["f_field"] = [row[0] for row in filters]
    params["f_op"] = [row[1] for row in filters]
    params["f_value"] = [row[2] for row in filters]

  columns = configuration.get("columns") or []
  if columns:
    params["fields"] = columns

  return params

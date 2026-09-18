-- v0.1.3: add expiry_date field type and copyable column to custom_fields,
-- and make field names case-insensitive (UNIQUE COLLATE NOCASE).
-- SQLite cannot alter a CHECK constraint, so the table is rebuilt.
-- Name allocation is provided by the migration runner so legacy case
-- collisions can be repaired without losing field identity or values.
CREATE TABLE custom_fields_new (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE,
  field_type TEXT NOT NULL CHECK (
    field_type IN (
      'text',
      'integer',
      'decimal',
      'boolean',
      'date',
      'expiry_date',
      'enum',
      'user'
    )
  ),
  description TEXT,
  required INTEGER NOT NULL DEFAULT 0 CHECK (required IN (0, 1)),
  enum_values TEXT,
  copyable INTEGER NOT NULL DEFAULT 0 CHECK (copyable IN (0, 1)),
  archived_at TEXT
);

CREATE TEMP TABLE custom_field_migration_names (
  id INTEGER PRIMARY KEY,
  old_name TEXT NOT NULL,
  new_name TEXT NOT NULL
);

INSERT INTO custom_field_migration_names (id, old_name, new_name)
SELECT id, name, migration_custom_field_name(id, name)
FROM custom_fields
ORDER BY id;

INSERT INTO custom_fields_new (
  id,
  name,
  field_type,
  description,
  required,
  enum_values,
  archived_at
)
SELECT
  fields.id,
  names.new_name,
  fields.field_type,
  fields.description,
  fields.required,
  fields.enum_values,
  fields.archived_at
FROM custom_fields AS fields
INNER JOIN custom_field_migration_names AS names ON names.id = fields.id;

INSERT INTO audit_log (
  user_id,
  action,
  entity_type,
  entity_id,
  details,
  timestamp
)
SELECT
  (SELECT id FROM users ORDER BY id LIMIT 1),
  'renamed',
  'custom_field',
  CAST(id AS TEXT),
  json_object('old_name', old_name, 'new_name', new_name),
  datetime('now')
FROM custom_field_migration_names
WHERE old_name != new_name
  AND EXISTS (SELECT 1 FROM users);

DROP TABLE custom_fields;
ALTER TABLE custom_fields_new RENAME TO custom_fields;

-- v0.1.3: add archival reason and notes to inventory_items.
ALTER TABLE inventory_items ADD COLUMN archival_reason TEXT CHECK (
  archival_reason IN ('Invalid', 'Damaged', 'Disposed')
);
ALTER TABLE inventory_items ADD COLUMN archival_notes TEXT;

DROP TABLE custom_field_migration_names;

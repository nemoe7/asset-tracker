-- v0.1.3: add expiry_date field type and copyable column to custom_fields.
-- SQLite cannot alter a CHECK constraint, so the table is rebuilt.
PRAGMA foreign_keys = OFF;

CREATE TABLE custom_fields_new (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
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
  id,
  name,
  field_type,
  description,
  required,
  enum_values,
  archived_at
FROM custom_fields;

DROP TABLE custom_fields;
ALTER TABLE custom_fields_new RENAME TO custom_fields;

PRAGMA foreign_keys = ON;

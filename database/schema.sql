CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  username TEXT NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT
);


CREATE TABLE roles (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);


CREATE TABLE permissions (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT
);


CREATE TABLE locations (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);


CREATE TABLE inventory_items (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  location_id INTEGER,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  archived_at TEXT,
  FOREIGN KEY (location_id)
    REFERENCES locations(id)
    ON DELETE SET NULL
);


CREATE TABLE custom_fields (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  field_type TEXT NOT NULL,
  description TEXT
);


CREATE TABLE user_roles (
  user_id INTEGER NOT NULL,
  role_id INTEGER NOT NULL,
  PRIMARY KEY (user_id, role_id),
  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,
  FOREIGN KEY (role_id)
    REFERENCES roles(id)
    ON DELETE CASCADE
);


CREATE TABLE role_permissions (
  role_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  PRIMARY KEY (role_id, permission_id),
  FOREIGN KEY (role_id)
    REFERENCES roles(id)
    ON DELETE CASCADE,
  FOREIGN KEY (permission_id)
    REFERENCES permissions(id)
    ON DELETE CASCADE
);


CREATE TABLE user_permissions (
  user_id INTEGER NOT NULL,
  permission_id INTEGER NOT NULL,
  allowed INTEGER NOT NULL,
  PRIMARY KEY (user_id, permission_id),
  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE CASCADE,
  FOREIGN KEY (permission_id)
    REFERENCES permissions(id)
    ON DELETE CASCADE
);


CREATE TABLE inventory_item_fields (
  item_id TEXT NOT NULL,
  field_id INTEGER NOT NULL,
  value TEXT,
  PRIMARY KEY (item_id, field_id),
  FOREIGN KEY (item_id)
    REFERENCES inventory_items(id)
    ON DELETE CASCADE,
  FOREIGN KEY (field_id)
    REFERENCES custom_fields(id)
    ON DELETE CASCADE
);


CREATE TABLE checks (
  id INTEGER PRIMARY KEY,
  item_id TEXT NOT NULL,
  user_id INTEGER NOT NULL,
  checked_at TEXT NOT NULL,
  FOREIGN KEY (item_id)
    REFERENCES inventory_items(id)
    ON DELETE RESTRICT,
  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE RESTRICT
);


CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL,
  action TEXT NOT NULL,
  entity_type TEXT NOT NULL,
  entity_id TEXT NOT NULL,
  details TEXT,
  timestamp TEXT NOT NULL,
  FOREIGN KEY (user_id)
    REFERENCES users(id)
    ON DELETE RESTRICT
);

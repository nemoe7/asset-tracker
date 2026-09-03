# Database Schema

This diagram is generated from [`schema.dbml`](./schema.dbml), which is the
source of truth for the database schema. The executable schema lives at
[`database/schema.sql`](../../database/schema.sql).

```mermaid
---
config:
  layout: elk
  elk:
    nodePlacementStrategy: LINEAR_SEGMENTS
---
erDiagram
    direction LR
    users {
        integer id PK
        text username UK "NOT NULL"
        text name "NOT NULL"
        text password_hash "NOT NULL"
        text created_at "NOT NULL"
        text updated_at "NOT NULL"
        text archived_at
    }
    roles {
        integer id PK
        text name UK "NOT NULL"
        text description
    }
    permissions {
        integer id PK
        text name UK "NOT NULL"
        text description
    }
    locations {
        integer id PK
        text name UK "NOT NULL"
        text description
        text created_at "NOT NULL"
        text updated_at "NOT NULL"
    }
    inventory_items {
        text id PK
        text name "NOT NULL"
        integer location_id FK "nullable, ON DELETE SET NULL"
        text description
        text created_at "NOT NULL"
        text updated_at "NOT NULL"
        text archived_at
    }
    custom_fields {
        integer id PK
        text name UK "NOT NULL"
        text field_type "NOT NULL, CHECK in (text, integer, decimal, boolean, date, enum, user)"
        text description
        integer required "NOT NULL DEFAULT 0, CHECK in (0, 1)"
        text enum_values
        text archived_at
    }
    user_roles {
        integer user_id PK, FK "ON DELETE CASCADE"
        integer role_id PK, FK "ON DELETE CASCADE"
    }
    role_permissions {
        integer role_id PK, FK "ON DELETE CASCADE"
        integer permission_id PK, FK "ON DELETE CASCADE"
        integer allowed "NOT NULL, CHECK in (0, 1)"
    }
    user_permissions {
        integer user_id PK, FK "ON DELETE CASCADE"
        integer permission_id PK, FK "ON DELETE CASCADE"
        integer allowed "NOT NULL, CHECK in (0, 1)"
    }
    inventory_item_fields {
        text item_id PK, FK "ON DELETE CASCADE"
        integer field_id PK, FK "ON DELETE CASCADE"
        text value
    }
    audit_log {
        integer id PK
        integer user_id FK "ON DELETE RESTRICT"
        text action "NOT NULL"
        text entity_type "NOT NULL"
        text entity_id "NOT NULL"
        text details
        text timestamp "NOT NULL"
    }
    export_templates {
        integer id PK
        integer user_id FK "nullable, ON DELETE SET NULL"
        text name "NOT NULL"
        text configuration "NOT NULL"
        text created_at "NOT NULL"
        text updated_at "NOT NULL"
    }
    backup_config {
        integer id PK "Singleton: id must always equal 1"
        integer enabled "NOT NULL DEFAULT 0, CHECK in (0, 1)"
        text schedule "NOT NULL"
        text backup_location "NOT NULL"
        text updated_at "NOT NULL"
    }
    backup_history {
        integer id PK
        integer user_id FK "nullable, ON DELETE SET NULL"
        text scheduled_at
        text completed_at "NOT NULL"
        text path "NOT NULL"
    }

    users ||--o{ user_roles : "has"
    roles ||--o{ user_roles : "assigned to"
    roles ||--o{ role_permissions : "grants"
    permissions ||--o{ role_permissions : "granted via"
    users ||--o{ user_permissions : "granted"
    permissions ||--o{ user_permissions : "granted via"
    inventory_items }o..o| locations : "located at"
    inventory_items ||--o{ inventory_item_fields : "has"
    custom_fields ||--o{ inventory_item_fields : "populates"
    users ||--o{ audit_log : "performs"
    users |o..o{ export_templates : "owns"
    users |o..o{ backup_history : "triggers"
```

Notes:

- Dashed lines (`..`) indicate optional (nullable) foreign keys.
- `backup_config` is a singleton table: `id` must always equal `1`.
- `check` constraints and `on delete` actions shown in quotes are enforced in
  `database/schema.sql`.

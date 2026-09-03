# Implementation Status

## Legend

- **🟢** — implementation and relevant frontend, backend, and tests are complete.
- **🟡** — some implementation exists, but the complete requirement is not yet satisfied.
- **🔴** — no complete implementation identified yet.
- **Requires** — requirements that this requirement relies on.
- **Related** — requirements that overlap in implementation or behavior.
- **Notes** — implementation details, gaps, or verification notes.

### P1

| ID⠀⠀⠀⠀⠀ | Prio | Description | Status | Requires | Related | Notes |
| ----- | :---: | ----- | :---: | ----- | ----- | -------- |
| AST-001 | P1 | Authorized users can create assets. | 🟢 | FLD-001, AUT-003 | AUD-001 | |
| AST-002 | P1 | Authorized users can view assets. | 🟢 | AUT-004 | SRH-004, SRH-005 | |
| AST-003 | P1 | Authorized users can edit assets according to permissions. | 🟢 | AUT-003, FLD-013 | AUD-002, CHK-007 | |
| AST-004 | P1 | Authorized users can archive assets. | 🟢 | AUT-003 | AUD-003, USE-005 | |
| AST-005 | P1 | Generate a unique Asset ID for each asset. | 🟢 | — | QRC-001, QRC-003 | |
| AST-006 | P1 | Asset ID is a UUID. | 🟢 | AST-005 | QRC-003 | |
| AST-007 | P1 | Validate required asset information. | 🟢 | FLD-001 | REL-001, REL-003 | |
| AST-008 | P1 | Prevent duplicate Asset IDs. | 🟢 | AST-005 | QRC-003 | |
| AST-009 | P1 | Archived assets remain available to authorized users. | 🟢 | AST-004, AUT-004 | AST-010, CHK-009 | |
| AST-010 | P1 | Archived assets are distinguishable from active assets. | 🟢 | AST-004 | AST-009, CHK-009 | |
| AST-011 | P1 | Normal inventory functions cannot permanently delete assets. | 🟢 | AST-004 | — | |
| AST-012 | P1 | Authorized users can restore archived assets. | 🟢 | AST-004, AUT-003 | AUD-003, USE-005 | |
| AST-013 | P1 | Retain asset information needed for inventory/insurance. | 🟢 | FLD-001 | — | |
| FLD-001 | P1 | Provide required built-in asset fields. | 🟢 | — | AST-001, AST-007, AST-013 | |
| FLD-002 | P1 | Admins can create custom asset fields. | 🟢 | — | FLD-003 | |
| FLD-003 | P1 | Admins can name custom fields. | 🟢 | FLD-002 | — | |
| QRC-001 | P1 | Associate each asset with a unique Asset ID. | 🟢 | AST-005 | QRC-003 | |
| QRC-002 | P1 | Encode Asset ID in the QR code. | 🟢 | QRC-001 | QRC-006 | QR generation to be handled externally |
| QRC-003 | P1 | Asset ID uniquely identifies its asset. | 🟢 | AST-005, AST-008 | QRC-001, CHK-002 | |
| QRC-004 | P1 | Support QR scanning on mobile devices. | 🟢 | — | CHK-001, CMP-003, USE-003 | |
| QRC-005 | P1 | Scanning opens the corresponding asset record. | 🟢 | QRC-004, CHK-002 | PER-003 | |
| QRC-006 | P1 | Provide information needed for an asset identification sticker. | 🟢 | QRC-001 | QRC-002 | Only Asset ID is the QR payload |
| CHK-001 | P1 | Checker can scan an asset QR code on mobile. | 🟢 | QRC-004 | USE-003 | |
| CHK-002 | P1 | Identify asset from scanned Asset ID. | 🟢 | QRC-001, QRC-003 | QRC-005 | |
| CHK-003 | P1 | Record scan events. | 🟢 | CHK-002 | AUD-004 | |
| CHK-004 | P1 | Record the user performing the scan. | 🟢 | CHK-003 | AUD-008 | |
| CHK-005 | P1 | Record scan date/time. | 🟢 | CHK-003 | AUD-009 | |
| CHK-006 | P1 | Indicate when scanned Asset ID does not exist. | 🟢 | CHK-002 | QRC-003 | |
| CHK-007 | P1 | Checker can update permitted information after scanning. | 🟢 | CHK-002, AUT-003 | AST-003, FLD-013 | |
| CHK-008 | P1 | Record changes resulting from an asset check. | 🟢 | CHK-007 | AUD-002, AUD-010 | |
| CHK-009 | P1 | Handle archived assets according to status/permissions. | 🟢 | AST-009, AUT-004 | AST-010 | |
| SRH-001 | P1 | Users can search assets. | 🟢 | AST-002 | SRH-004 | |
| SRH-002 | P1 | Users can filter assets using available fields. | 🟢 | AST-002 | SRH-006 | |
| SRH-003 | P1 | Users can sort asset results. | 🟢 | AST-002 | SRH-004 | |
| SRH-004 | P1 | Display assets in a tabular/equivalent inventory view. | 🟢 | AST-002 | SRH-001, SRH-003 | |
| SRH-005 | P1 | Open an individual asset from the inventory view. | 🟢 | AST-002 | QRC-005 | |
| SRH-006 | P1 | Filters affect displayed results and applicable exports. | 🟢 | SRH-002 | EXP-004 | |
| AUD-001 | P1 | Record asset creation events. | 🟢 | AST-001 | AUD-009 | |
| AUD-002 | P1 | Record asset modification events. | 🟢 | AST-003 | CHK-008 | |
| AUD-003 | P1 | Record asset archival/restoration events. | 🟢 | AST-004, AST-012 | USE-005 | |
| AUD-004 | P1 | Record asset QR scan events. | 🟢 | CHK-003 | CHK-004, CHK-005 | |
| AUD-009 | P1 | Record date/time for each audit event. | 🟢 | AUD-001–004 | CHK-005 | |
| EXP-001 | P1 | Authorized users can export inventory. | 🟢 | AUT-003 | EXP-002 | |
| EXP-002 | P1 | Provide Excel-compatible export. | 🟢 | EXP-001 | — | |
| EXP-003 | P1 | Allow field selection for exports. | 🟢 | EXP-001 | FLD-014 | |
| EXP-004 | P1 | Allow filtered inventory exports. | 🟢 | EXP-001, SRH-006 | SRH-002 | |
| IMP-001 | P1 | Authorized users can import asset records. | 🔴 | AUT-003 | IMP-002–004 | |
| IMP-002 | P1 | An import requires at minimum an Asset Name. | 🔴 | IMP-001 | AST-007 | |
| IMP-003 | P1 | Generate an Asset ID for imported assets when one is not provided. | 🔴 | IMP-001, AST-005 | QRC-001 | |
| IMP-004 | P1 | Optional fields not supplied during import remain unset. | 🔴 | IMP-001 | FLD-001 | |
| BKP-011 | P1 | Authorized users can create manual backups. | 🔴 | AUT-003 | BKP-014, REL-004, SEC-006 | |
| BKP-012 | P1 | Authorized users can restore from a valid backup. | 🔴 | AUT-003, BKP-010 | BKP-013, REL-004, SEC-006 | |
| BKP-013 | P1 | Warn before restoration that may overwrite data. | 🔴 | BKP-012 | USE-005 | |
| REL-004 | P1 | Valid backup is sufficient to restore required data. | 🔴 | BKP-010, BKP-012 | REL-005 | |
| REL-005 | P1 | Never report backup success before successful completion. | 🔴 | BKP-011 | BKP-015 | |
| USE-002 | P1 | Provide a desktop-oriented management experience. | 🟢 | — | USE-003 | |
| USE-003 | P1 | Provide a mobile-oriented checking/scanning experience. | 🟢 | QRC-004, CHK-001 | CMP-002, CMP-003 | |

### P3

| ID⠀⠀⠀⠀⠀ | Prio | Description | Status | Requires | Related | Notes |
| ----- | :---: | ----- | :---: | ----- | ----- | -------- |
| AUD-005 | P3 | Record custom-field creation/modification/deactivation. | 🟢 | FLD-002, FLD-009, FLD-010 | FLD-015 | |
| AUD-006 | P3 | Record user/role/permission changes. | 🟡 | USR-001–007 | USR-013 | UI pending |
| AUD-007 | P3 | Record backup/restoration events. | 🔴 | BKP-011, BKP-012 | BKP-014 | |
| AUD-008 | P3 | Record user responsible for each event. | 🟢 | — | CHK-004 | |
| AUD-010 | P3 | Record affected field and previous/new values. | 🟢 | AUD-002 | CHK-008 | |
| AUD-011 | P3 | Authorized users can view audit/activity logs on desktop/mobile. | 🔴 | AUT-003 | USR-012, AUD-012 | route/UI pending |
| AUD-013 | P3 | Audit logs cannot be edited normally. | 🟢 | — | SEC-005 | |
| BKP-007 | P3 | Perform missed scheduled backup on next startup. | 🔴 | BKP-006 | REL-007 | |
| BKP-010 | P3 | System backup includes all required application data. | 🔴 | — | REL-004 | |
| BKP-014 | P3 | Record backup/restoration events. | 🔴 | BKP-011, BKP-012 | AUD-007 | |
| CMP-001 | P3 | Support current common desktop browsers. | 🟡 | USE-001 | — | Test browser compatibility |
| CMP-002 | P3 | Support modern mobile browsers. | 🟡 | USE-003 | QRC-004 | Test mobile browser compatibility |
| CMP-003 | P3 | QR scanning works through supported mobile cameras/browser functionality. | 🟢 | QRC-004 | CHK-001 | |
| FLD-006 | P3 | Admins can define Enum values. | 🟢 | FLD-004, FLD-005 | FLD-002 | |
| FLD-008 | P3 | Admins can mark custom fields required. | 🟢 | FLD-002, FLD-004 | FLD-012 | |
| FLD-011 | P3 | Deactivating a field preserves existing values. | 🟢 | FLD-010 | — | |
| FLD-015 | P3 | Record changes to custom-field definitions. | 🟢 | FLD-002, FLD-009, FLD-010 | AUD-005 | |
| PER-001 | P3 | Normal inventory operations respond reasonably. | 🟡 | — | PER-002, PER-003 | No explicit performance target/test established |
| PER-002 | P3 | Search/filtering does not require manual reload. | 🟢 | SRH-001, SRH-002 | — | |
| PER-003 | P3 | QR scanning opens the asset without unnecessary steps. | 🟢 | QRC-005 | CHK-001 | |
| SEC-001 | P3 | Protected functions require authentication. | 🟢 | AUT-006 | — | |
| SEC-002 | P3 | Enforce role/per-user access control. | 🟡 | AUT-003 | AUT-005, SEC-003 | |
| SEC-003 | P3 | Users only access permitted information/functions. | 🟡 | AUT-003, AUT-004 | SEC-002 | |
| SEC-004 | P3 | Credentials are not stored in plaintext. | 🟢 | AUT-001 | — | |
| SEC-005 | P3 | Audit logs are protected from unauthorized modification. | 🟢 | — | AUD-013 | |
| SEC-007 | P3 | Backup files are protected from unauthorized access. | 🔴 | BKP-011 | SEC-006 | |
| SEC-008 | P3 | Custom fields cannot bypass integrity/security controls. | 🔴 | FLD-012, FLD-013 | — | Revisit custom fields |
| QRC-007 | P3 | QR code contains the Asset ID and does not need to contain the asset's complete information. | 🟢 | QRC-001 | QRC-002, QRC-006 | |
| SRH-007 | P3 | Custom fields can be used for search/filtering. | 🟢 | FLD-014 | SRH-002 | User-type fields excluded (FLD-007 pending) |
| USE-001 | P3 | Application usable through a standard web browser. | 🟢 | — | CMP-001, CMP-002 | |
| USE-004 | P3 | Common asset operations require minimal navigation. | 🟡 | AST-001–004, QRC-005 | PER-003 | |
| REL-003 | P3 | Maintain data integrity when creating/modifying records. | 🟢 | AST-007 | REL-001 | |
| REL-006 | P3 | Retain information identifying most recent successful backup. | 🔴 | BKP-015 | BKP-009 | |

### P4

| ID⠀⠀⠀⠀⠀ | Prio | Description | Status | Requires | Related | Notes |
| ----- | :---: | ----- | :---: | ----- | ----- | -------- |
| AUT-001 | P4 | Users can log in with assigned credentials. | 🟢 | — | SEC-004 | |
| AUT-002 | P4 | Users can log out. | 🟢 | AUT-001 | — | |
| AUT-006 | P4 | Unauthenticated users cannot access protected functionality. | 🟢 | — | SEC-001 | |
| USR-001 | P4 | Admins can create users. | 🟡 | AUT-003 | USR-002, USR-003, USR-005 | UI pending |
| USR-002 | P4 | Admins can modify users. | 🟡 | USR-001 | — | UI pending |
| USR-003 | P4 | Admins can deactivate users. | 🟡 | USR-001 | — | UI pending |
| USR-004 | P4 | Admins can create/manage roles. | 🟡 | AUT-003 | USR-005, USR-006 | route/UI pending |
| USR-005 | P4 | Admins can assign roles to users. | 🟡 | USR-001, USR-004 | AUT-003 | route/UI pending |
| USR-006 | P4 | Admins can configure role permissions. | 🟡 | USR-004 | AUT-003 | route/UI pending |
| USR-007 | P4 | Admins can configure per-user overrides. | 🔴 | USR-001 | USR-008, AUT-013 | |
| USR-012 | P4 | Admins can configure audit-log visibility. | 🔴 | USR-004 | AUD-011, AUD-012 | |
| USR-013 | P4 | Record user/role/permission changes. | 🟡 | USR-001–007 | AUD-006 | UI pending |
| FLD-004 | P4 | Admins can specify custom-field data type. | 🟢 | FLD-002, FLD-003 | FLD-005 | |
| FLD-005 | P4 | Support Text, Integer, Decimal, Boolean, Date, Enum, User. | 🟢 | FLD-004 | FLD-006, FLD-007, FLD-012 | |
| FLD-009 | P4 | Admins can modify custom-field configuration. | 🟢 | FLD-002 | FLD-015 | |
| FLD-010 | P4 | Admins can deactivate custom fields. | 🟢 | FLD-002 | FLD-011, FLD-015 | |
| FLD-014 | P4 | Custom fields available for search/filter/export. | 🟢 | FLD-002, FLD-004 | SRH-007, EXP-003 | User-type fields excluded (FLD-007 pending) |
| EXP-005 | P4 | Authorized users can create saved export templates. | 🔴 | EXP-001 | EXP-006, EXP-007 | |
| EXP-006 | P4 | Export templates contain filters and field selections. | 🔴 | EXP-005 | EXP-007 | |
| EXP-007 | P4 | Users can apply saved export templates. | 🔴 | EXP-005, EXP-006 | — | |
| EXP-008 | P4 | Export templates support custom fields. | 🔴 | EXP-005, FLD-014 | — | |
| IMP-005 | P4 | Validate imported values against field types/requirements. | 🔴 | IMP-001, FLD-005, FLD-008, FLD-012 | REL-001 | |
| IMP-006 | P4 | Report rejected records without corrupting inventory. | 🔴 | IMP-001, REL-001 | — | |
| IMP-007 | P4 | Record imports in the audit log. | 🔴 | IMP-001 | AUD-006 | |
| REL-001 | P4 | Invalid input does not corrupt inventory data. | 🟢 | AST-007 | IMP-006, REL-003 | |

### P5

| ID⠀⠀⠀⠀⠀ | Prio | Description | Status | Requires | Related | Notes |
| ----- | :---: | ----- | :---: | ----- | ----- | -------- |
| AUT-003 | P5 | Restrict functionality according to roles/permissions. | 🟡 | — | SEC-002 | |
| AUT-004 | P5 | Restrict asset information according to permissions. | 🟡 | AUT-003 | SEC-003, FLD-013 | |
| AUT-005 | P5 | Same permission rules on desktop/mobile. | 🟡 | AUT-003, AUT-004 | SEC-003, USE-003 | |
| AUT-012 | P5 | Wildcards automatically apply to newly created matching permissions. | 🟢 | AUT-008 | AUT-009 | |
| AUT-013 | P5 | Direct user decisions override role permissions. | 🟢 | USR-008 | AUT-003 | |
| AUT-014 | P5 | Most-specific matching permission wins. | 🟢 | AUT-008 | AUT-015 | |
| AUT-015 | P5 | Equal-specificity conflicting role permissions deny. | 🟢 | AUT-003 | AUT-014 | |
| AUT-016 | P5 | Permission changes apply on subsequent checks without re-login. | 🟢 | AUT-003 | — | |
| AUT-017 | P5 | Authorization checks use `namespace.operation`. | 🟢 | AUT-007 | — | |
| AUD-012 | P5 | Restrict audit-log visibility by permission. | 🔴 | USR-012, AUT-003 | AUD-011 | |
| BKP-001 | P5 | Automatic backups disabled by default. | 🔴 | — | BKP-003 | |
| BKP-002 | P5 | Prompt Admin to configure backups on first initialization. | 🔴 | BKP-001 | — | |
| BKP-003 | P5 | Admins can enable/disable automatic backups. | 🔴 | BKP-001 | BKP-004 | |
| BKP-004 | P5 | Admins can configure backup schedule. | 🔴 | BKP-003 | BKP-005 | |
| BKP-005 | P5 | Default schedule is Sunday 03:00 weekly. | 🔴 | BKP-004 | — | |
| BKP-006 | P5 | Detect missed scheduled backups. | 🔴 | BKP-004 | BKP-007, BKP-008 | |
| BKP-008 | P5 | Avoid duplicate backups for a scheduled period. | 🔴 | BKP-006 | — | |
| BKP-009 | P5 | Record scheduled and actual backup times. | 🔴 | BKP-006 | AUD-007, REL-006 | |
| BKP-015 | P5 | Provide backup status/confirmation. | 🔴 | BKP-011 | REL-005, REL-006 | |
| BKP-016 | P5 | Configurable backup storage location. | 🔴 | — | BKP-017, BKP-018 | |
| BKP-017 | P5 | Default backup location is mounted deployment directory. | 🔴 | BKP-016 | — | |
| BKP-018 | P5 | Backup location configurable independently of runtime. | 🔴 | BKP-016 | BKP-019 | |
| BKP-019 | P5 | Support external backup locations such as NAS where practical. | 🔴 | BKP-018 | — | |
| EXP-009 | P5 | Export only information available to generating user. | 🔴 | EXP-001, AUT-004 | SEC-003 | |
| FLD-012 | P5 | Validate custom-field values against configured type. | 🟢 | FLD-005 | SEC-008, IMP-005 | |
| FLD-013 | P5 | Custom fields respect viewing/editing permissions. | 🔴 | FLD-002, AUT-004 | USR-009, USR-010 | |
| REL-002 | P5 | Failed operations provide appropriate errors. | 🟡 | — | — | Complete coverage is not established |
| REL-007 | P5 | Missed scheduled backup recoverable at startup. | 🔴 | BKP-007 | BKP-006 | |
| SEC-006 | P5 | Restrict backup/restore to authorized users. | 🔴 | BKP-011, BKP-012, AUT-003 | SEC-001 | |
| USE-005 | P5 | Archive/restore require confirmation. | 🟢 | AST-004, AST-012 | BKP-013 | |
| USE-006 | P5 | Backup UI shows enabled state and next scheduled backup. | 🔴 | BKP-015 | BKP-004 | |
| AUT-007 | — | Support exact permission grants. | 🟢 | — | AUT-017 | |
| AUT-008 | — | Support `namespace.*` wildcard grants. | 🟢 | — | AUT-009, AUT-012 | |
| AUT-009 | — | Namespace wildcard grants all concrete namespace permissions. | 🟢 | AUT-008 | AUT-012 | |
| AUT-010 | — | Support global `*` wildcard. | 🟢 | — | AUT-011 | |
| AUT-011 | — | Global wildcard grants all concrete permissions. | 🟢 | AUT-010 | AUT-012 | |
| USR-008 | — | Per-user permissions override inherited role permissions. | 🟢 | USR-007 | AUT-013 | |
| USR-009 | — | Configure which asset fields Checkers can view. | 🔴 | FLD-002, FLD-013 | USR-010 | |
| USR-010 | — | Configure which asset fields Checkers can edit. | 🔴 | FLD-002, FLD-013 | USR-009 | |
| USR-011 | — | Checkers cannot modify their own permissions. | 🔴 | USR-007 | — | |
| FLD-007 | — | User custom fields reference system users. | 🟡 | FLD-005 | USR-001 | UI pending |

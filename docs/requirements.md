# Inventory Management

**Client:** The Birth-Giver
**Developer:** nemoe7
**Version:** 0.5
**Last Updated:** 2026-08-25

## 1. Introduction

### 1.1 Purpose

The purpose of the system is to maintain a complete and organized record of office inventory, including equipment, furniture, IT equipment, and other high-value assets.

The system will provide a central inventory database, simplify physical asset checking and identification, maintain an audit trail of system activity and asset changes, and provide export, backup, and restoration capabilities. The inventory data may also be used as supporting documentation for insurance purposes.

### 1.2 Scope

The system will provide a browser-based application for managing office assets.

The system will support:

- Asset creation, viewing, editing, and archival.
- User authentication and access control.
- User and permission management.
- Configurable asset fields.
- Asset search, filtering, and sorting.
- QR-code-based asset identification and scanning.
- Separate desktop and mobile interfaces.
- Mobile asset checking and updating.
- Audit and activity logging.
- Excel-compatible export.
- Filtered and customizable exports.
- Scheduled and manual backups.
- Full-system backup and restoration.

### 1.3 Users

The system will have the following user roles:

- **Office Admins** — manage inventory, users, permissions, asset fields, exports, backups, restoration, and system configuration.
- **Checkers** — inspect assets, perform QR scans, and view or update asset information according to their assigned permissions.

Access to functionality shall be determined by user permissions rather than by device type.

---

## 2. System Overview

The application will provide a browser-based interface with separate desktop and mobile experiences.

### Desktop

The desktop interface will primarily provide functionality for:

- Inventory management.
- Searching and filtering assets.
- Managing users and permissions.
- Managing asset fields.
- Reviewing logs.
- Creating exports.
- Managing backups and restoration.

### Mobile

The mobile interface will primarily provide functionality for:

- Scanning asset QR codes.
- Viewing asset information.
- Updating permitted asset fields.
- Recording asset checks.
- Viewing relevant asset history.
- Viewing audit and activity logs when permitted.

The availability of a function shall depend on the user's permissions, not solely on whether the user is using a desktop or mobile device.

## 2.1 Main Features

- User authentication and access control.
- User management and permissions.
- Asset management.
- Configurable asset fields.
- Asset search, filtering, and sorting.
- QR-code asset identification.
- Mobile QR scanning.
- Physical asset checking.
- Audit and activity logs.
- Field-level change tracking.
- Excel-compatible export.
- Saved export filter templates.
- Scheduled and manual backups.
- Full-system backup and restore.

## 2.2 Typical User Flows

### 2.2.1 Desktop — Inventory Management

1. The user logs into the application.
2. The system displays the desktop interface according to the user's permissions.
3. The user searches for, filters, or selects an asset.
4. The user views or modifies the asset as permitted.
5. The system records applicable changes in the audit log.

### 2.2.2 Desktop — Log Review

1. The user logs into the application.
2. The user opens the audit or activity log.
3. The system displays log entries permitted by the user's permissions.
4. The user filters or reviews the available entries.
5. The user may open an individual entry to view additional details.

### 2.2.3 Desktop — Field Management

1. An Office Admin logs into the application.
2. The Admin opens asset field management.
3. The Admin creates or modifies a custom field.
4. The Admin specifies the field name, type, and applicable configuration.
5. The Admin configures the permissions applicable to the field.
6. The system makes the field available according to its configuration and permissions.

### 2.2.4 Mobile — Asset Checking

1. The user logs into the application.
2. The system displays the mobile interface according to the user's permissions.
3. The user opens the QR scanner.
4. The user scans an asset QR code.
5. The system identifies the asset using its Asset ID.
6. The system displays the asset information available to the user.
7. The user checks or updates permitted information.
8. The system records the scan and any resulting changes.

### 2.2.5 Mobile — Asset Viewing

1. The user logs into the application.
2. The user searches for or selects an asset.
3. The system displays the asset information available to the user.
4. The user may update permitted fields.

### 2.2.6 Mobile — Log Review

1. The user logs into the application.
2. The user opens the audit or activity log if permitted.
3. The system displays log entries accessible to the user.
4. The user filters or reviews the available entries.
5. The user may open an individual entry to view additional details.

### 2.2.7 Export

1. An authorized user opens the inventory view.
2. The user applies filters and/or selects the fields to export.
3. The user selects a saved export template or configures the filters manually.
4. The system generates the export file.
5. The user downloads the resulting file.

### 2.2.8 Backup and Restore

1. An authorized user opens the backup or restore interface.
2. The user selects the required operation.
3. The system performs the backup or validates the selected backup.
4. The system displays the operation result.
5. The system records the operation in the audit log.

---

## 3. Functional Requirements

### 3.1 Authentication and Access Control

The system shall authenticate users and enforce their assigned permissions.

- **AUT-001** `[P4]`: The system shall allow users to log in using their assigned credentials.
- **AUT-002** `[P4]`: The system shall provide a mechanism for users to log out.
- **AUT-003** `[P5]`: The system shall restrict functionality according to the user's assigned roles and permissions.
- **AUT-004** `[P5]`: The system shall restrict access to asset information according to the user's permissions.
- **AUT-005** `[P5]`: The system shall enforce the same permission rules on supported desktop and mobile interfaces.
- **AUT-006** `[P4]`: The system shall prevent unauthenticated users from accessing protected functionality.
- **AUT-007**: The system shall support exact permission grants.
- **AUT-008**: The system shall support namespace wildcard grants using the `namespace.*` format.
- **AUT-009**: A namespace wildcard grant shall grant access to all concrete permissions within that namespace.
- **AUT-010**: The system shall support the global wildcard grant `*`.
- **AUT-011**: A global wildcard grant shall grant access to all concrete permissions.
- **AUT-012**: Wildcard grants shall automatically apply to newly created concrete permissions that match the wildcard.
- **AUT-013**: Direct user permission decisions shall take precedence over permissions inherited from roles.
- **AUT-014**: When multiple permissions from the same source match a requested permission, the most specific matching permission shall take precedence.
- **AUT-015**: When conflicting role permissions have equal specificity, a deny decision shall take precedence.
- **AUT-016**: Permission changes shall take effect on subsequent authorization checks without requiring the affected user to authenticate again.
- **AUT-017**: Permission checks shall request concrete permissions using the `namespace.operation` format.

### 3.2 User Management and Permissions

Office Admins shall be able to manage users and configure permissions.

- **USR-001** `[P4]`: Office Admins shall be able to create user accounts.
- **USR-002** `[P4]`: Office Admins shall be able to modify user accounts.
- **USR-003** `[P4]`: Office Admins shall be able to deactivate user accounts.
- **USR-004** `[P4]`: Office Admins shall be able to create and manage roles.
- **USR-005** `[P4]`: Office Admins shall be able to assign roles to users.
- **USR-006** `[P4]`: Office Admins shall be able to configure permissions for roles.
- **USR-007** `[P4]`: Office Admins shall be able to configure per-user permission overrides.
- **USR-008**: Per-user permissions shall be able to override the permissions inherited from the user's roles.
- **USR-009**: Office Admins shall be able to configure which asset fields Checkers can view.
- **USR-010**: Office Admins shall be able to configure which asset fields Checkers can edit.
- **USR-011**: Checkers shall not be able to modify their own permissions.
- **USR-012** `[P4]`: Office Admins shall be able to configure which users or roles can view audit and activity logs.
- **USR-013** `[P4]`: The system shall record relevant user, role, and permission changes in the audit log.

### 3.3 Asset Management

The system shall maintain records for office assets.

- **AST-001** `[P1]`: Authorized users shall be able to create an asset record.
- **AST-002** `[P1]`: Authorized users shall be able to view asset records.
- **AST-003** `[P1]`: Authorized users shall be able to edit asset records according to their permissions.
- **AST-004** `[P1]`: Authorized users with the appropriate permissions shall be able to archive asset records.
- **AST-005** `[P1]`: The system shall automatically generate a unique Asset ID for each new asset.
- **AST-006** `[P1]`: The Asset ID shall be a UUID.
- **AST-007** `[P1]`: The system shall validate required asset information before saving an asset.
- **AST-008** `[P1]`: The system shall prevent duplicate Asset IDs.
- **AST-009** `[P1]`: Archived assets shall remain available to authorized users for historical reference.
- **AST-010** `[P1]`: Archived assets shall be distinguishable from active assets.
- **AST-011** `[P1]`: The system shall not permanently delete an asset through normal inventory management functions.
- **AST-012** `[P1]`: Authorized users shall be able to restore an archived asset to an active state.
- **AST-013** `[P1]`: The system shall retain relevant asset information required for inventory and insurance purposes.

### 3.4 Configurable Asset Fields

The system shall provide a minimum set of built-in asset fields and allow Office Admins to define additional custom fields.

- **FLD-001** `[P1]`: The system shall provide the minimum built-in asset fields defined in Section 5.1.
- **FLD-002** `[P1]`: Office Admins shall be able to create custom asset fields.
- **FLD-003** `[P1]`: Office Admins shall be able to specify a name for each custom field.
- **FLD-004** `[P4]`: Office Admins shall be able to specify the data type of each custom field.
- **FLD-005** `[P4]`: The system shall support appropriate field types for the project's requirements, including at minimum:
  - Text
  - Integer
  - Decimal
  - Boolean
  - Date
  - Enum
  - User
- **FLD-006** `[P3]`: Office Admins shall be able to define the available values for an Enum field.
- **FLD-007**: A User field shall reference a user account within the system.
- **FLD-008** `[P3]`: Office Admins shall be able to specify whether a custom field is required.
- **FLD-009** `[P4]`: Office Admins shall be able to modify custom field configuration subject to data integrity constraints.
- **FLD-010** `[P4]`: Office Admins shall be able to deactivate a custom field.
- **FLD-011** `[P3]`: Deactivating a custom field shall not automatically remove existing values associated with that field.
- **FLD-012** `[P5]`: Custom field values shall be validated according to their configured data type.
- **FLD-013** `[P5]`: Custom fields shall be available for viewing and editing according to user permissions.
- **FLD-014** `[P4]`: Custom fields shall be available for searching, filtering, and exporting where applicable.
- **FLD-015** `[P3]`: Changes to custom field definitions shall be recorded in the audit log.

### 3.5 Asset Identification and QR Codes

Each asset shall be identified using its Asset ID, which is encoded in its QR code.

- **QRC-001** `[P1]`: The system shall associate each asset with a unique Asset ID.
- **QRC-002** `[P1]`: The Asset ID shall be encoded in the asset's QR code.
- **QRC-003** `[P1]`: The Asset ID shall uniquely identify its associated asset.
- **QRC-004** `[P1]`: The system shall support scanning asset QR codes using supported mobile devices.
- **QRC-005** `[P1]`: Scanning an asset QR code shall open the corresponding asset record.
- **QRC-006** `[P1]`: The system shall provide the information required to create an asset identification sticker.
- **QRC-007** `[P3]`: The QR code shall contain the Asset ID and shall not need to contain the asset's complete information.

### 3.6 Asset Checking and Scanning

The system shall support physical inventory checking through QR scanning.

- **CHK-001** `[P1]`: A Checker shall be able to scan an asset QR code using a supported mobile device.
- **CHK-002** `[P1]`: The system shall identify the asset from the scanned Asset ID.
- **CHK-003** `[P1]`: The system shall record the scan event.
- **CHK-004** `[P1]`: The system shall record the user who performed the scan.
- **CHK-005** `[P1]`: The system shall record the date and time of the scan.
- **CHK-006** `[P1]`: The system shall indicate when a scanned Asset ID does not correspond to an existing asset.
- **CHK-007** `[P1]`: A Checker shall be able to update permitted asset information after scanning.
- **CHK-008** `[P1]`: The system shall record changes resulting from an asset check.
- **CHK-009** `[P1]`: Archived assets shall be handled according to their status and the user's permissions when scanned.

### 3.7 Search, Filtering, and Inventory Views

The system shall provide database-like inventory views.

- **SRH-001** `[P1]`: Users shall be able to search for assets.
- **SRH-002** `[P1]`: Users shall be able to filter assets using available asset fields.
- **SRH-003** `[P1]`: Users shall be able to sort asset results using available fields.
- **SRH-004** `[P1]`: The system shall display asset information in a tabular or equivalent inventory view.
- **SRH-005** `[P1]`: The system shall allow users to open an individual asset from an inventory view.
- **SRH-006** `[P1]`: Applied filters shall affect the displayed results and filtered exports where applicable.
- **SRH-007** `[P3]`: Custom fields shall be available as search and filter criteria where applicable.

### 3.8 Audit and Activity Logs

The system shall maintain an audit trail of relevant system activity.

- **AUD-001** `[P1]`: The system shall record asset creation events.
- **AUD-002** `[P1]`: The system shall record asset modification events.
- **AUD-003** `[P1]`: The system shall record asset archival and restoration events.
- **AUD-004** `[P1]`: The system shall record asset QR scan events.
- **AUD-005** `[P3]`: The system shall record custom field creation, modification, and deactivation events.
- **AUD-006** `[P3]`: The system shall record user, role, and permission changes.
- **AUD-007** `[P3]`: The system shall record backup and restoration events.
- **AUD-008** `[P3]`: The system shall record the user responsible for each logged event.
- **AUD-009** `[P1]`: The system shall record the date and time of each logged event.
- **AUD-010** `[P3]`: For applicable asset changes, the system shall record the affected field and its previous and new values.
- **AUD-011** `[P3]`: Authorized users shall be able to view relevant audit and activity logs from supported desktop and mobile devices.
- **AUD-012** `[P5]`: The system shall restrict log visibility according to the user's permissions.
- **AUD-013** `[P3]`: Audit logs shall not be editable through normal inventory management functions.

### 3.9 Export

The system shall allow inventory information to be exported.

- **EXP-001** `[P1]`: Authorized users shall be able to export inventory data.
- **EXP-002** `[P1]`: The system shall provide an Excel-compatible export format.
- **EXP-003** `[P1]`: Users shall be able to select which fields are included in an export where supported.
- **EXP-004** `[P1]`: Users shall be able to export filtered inventory results.
- **EXP-005** `[P4]`: Authorized users shall be able to create saved export templates.
- **EXP-006** `[P4]`: An export template shall consist of a predefined set of filters and applicable export field selections.
- **EXP-007** `[P4]`: Users shall be able to apply a saved export template before generating an export.
- **EXP-008** `[P4]`: Export templates shall support configured custom fields.
- **EXP-009** `[P5]`: Exported data shall reflect the information available to the user generating the export.

Note: only CSV export is supported.

### 3.10 Import

The system shall support importing existing inventory data.

- **IMP-001** `[P1]`: Authorized users shall be able to import asset records.
- **IMP-002** `[P1]`: An import shall require, at minimum, an Asset Name for each imported asset.
- **IMP-003** `[P1]`: The system shall automatically generate an Asset ID for imported assets where one is not provided.
- **IMP-004** `[P1]`: Optional fields not supplied during import shall remain unset.
- **IMP-005** `[P4]`: The system shall validate imported values against the corresponding field types and requirements.
- **IMP-006** `[P4]`: The system shall report invalid or rejected records without corrupting existing inventory data.
- **IMP-007** `[P4]`: Import operations shall be recorded in the audit log.

### 3.11 Backup and Restore

The system shall support scheduled and manual backups and full-system restoration.

- **BKP-001** `[P5]`: Automatic backups shall be disabled by default.
- **BKP-002** `[P5]`: During first-time system initialization, the system shall prompt the Admin to configure automatic backups.
- **BKP-003** `[P5]`: Office Admins shall be able to enable or disable automatic backups.
- **BKP-004** `[P5]`: Office Admins shall be able to configure the automatic backup schedule.
- **BKP-005** `[P5]`: The default proposed schedule shall be once per week on Sunday at 03:00 when automatic backups are enabled.
- **BKP-006** `[P5]`: The system shall detect when a scheduled backup was missed because the application was not running at the scheduled time.
- **BKP-007** `[P3]`: If a scheduled backup was missed, the system shall perform the pending backup when the application next starts.
- **BKP-008** `[P5]`: The system shall avoid creating duplicate backups for the same scheduled backup period.
- **BKP-009** `[P5]`: The system shall record the scheduled backup time and the actual backup time.
- **BKP-010** `[P3]`: A system backup shall include:

  - Asset records.
  - User accounts.
  - Roles and permissions.
  - Custom field definitions and configuration.
  - Custom field values.
  - Audit and activity logs.
  - Relevant system configuration required for restoration.
- **BKP-011** `[P1]`: Authorized users shall be able to create a system backup manually.
- **BKP-012** `[P1]`: Authorized users shall be able to restore the system from a valid backup.
- **BKP-013** `[P1]`: The system shall warn users before a restoration that may overwrite existing data.
- **BKP-014** `[P3]`: The system shall record backup and restoration events in the audit log.
- **BKP-015** `[P5]`: The system shall provide backup status and confirmation information.
- **BKP-016** `[P5]`: The system shall maintain backup files in a configurable storage location.
- **BKP-017** `[P5]`: The default backup location shall be a directory mounted into the application deployment.
- **BKP-018** `[P5]`: The backup location shall be configurable independently of the application runtime.
- **BKP-019** `[P5]`: The system should support externally hosted backup locations such as NAS storage where practical.

---

## 4. Non-Functional Requirements

### 4.1 Performance

- **PER-001** `[P3]`: Normal inventory operations shall respond within a reasonable time under the expected number of users and assets.
- **PER-002** `[P3]`: Asset searches and filtering shall not require the user to manually reload the application.
- **PER-003** `[P3]`: QR scanning shall open the corresponding asset record without unnecessary intermediate steps.

### 4.2 Usability

- **USE-001** `[P3]`: The application shall be usable through a standard web browser.
- **USE-002** `[P1]`: The interface shall provide a desktop-oriented management experience.
- **USE-003** `[P1]`: The interface shall provide a mobile-oriented experience for asset checking and QR scanning.
- **USE-004** `[P3]`: Common asset operations shall require minimal navigation.
- **USE-005** `[P5]`: Archival and restoration operations shall require appropriate confirmation.
- **USE-006** `[P5]`: Backup configuration shall clearly indicate whether automatic backups are enabled and the next scheduled backup time.

### 4.3 Security

- **SEC-001** `[P3]`: Protected system functions shall require authentication.
- **SEC-002** `[P3]`: The system shall enforce role-based and per-user access control.
- **SEC-003** `[P3]`: Users shall only be able to access information and functions permitted by their effective permissions.
- **SEC-004** `[P3]`: Authentication credentials shall not be stored in plaintext.
- **SEC-005** `[P3]`: Audit logs shall be protected against modification by unauthorized users.
- **SEC-006** `[P5]`: Backup and restore functions shall be restricted to authorized users.
- **SEC-007** `[P3]`: Backup files shall be protected from unauthorized access.
- **SEC-008** `[P3]`: Custom field configuration shall not bypass the system's fundamental data integrity or security controls.

### 4.4 Compatibility

- **CMP-001** `[P3]`: The application shall support current versions of commonly used desktop web browsers.
- **CMP-002** `[P3]`: The application shall support modern mobile browsers on supported smartphones.
- **CMP-003** `[P1]`: QR scanning shall work with supported mobile device cameras or browser-based scanning functionality.

### 4.5 Reliability and Recovery

- **REL-001** `[P4]`: The system shall handle invalid user input without corrupting existing inventory data.
- **REL-002** `[P5]`: Failed operations shall provide an appropriate error message.
- **REL-003** `[P3]`: The system shall maintain data integrity when creating or modifying records.
- **REL-004** `[P1]`: A valid backup shall be sufficient to restore the required application data.
- **REL-005** `[P1]`: The system shall not report a backup as successful unless the backup operation has completed successfully.
- **REL-006** `[P3]`: The system shall retain sufficient information to determine when the most recent successful backup occurred.
- **REL-007** `[P5]`: A missed scheduled backup shall be recoverable on the next application startup.

---

## 5. Data Requirements

### 5.1 Minimum Asset Data

The system shall provide a minimum set of built-in asset fields. Additional fields may be configured by Office Admins.

| Data | Description | Required |
| --- | --- | --- |
| Asset ID | System-generated UUID, encoded in the asset's QR code | Yes |
| Name | Name or basic description of the asset | Yes |
| Location | Current location of the asset | Yes |
| Created At | Date and time the record was created | Yes |
| Updated At | Date and time the record was last modified | Yes |

Location shall support a value representing an unset or unknown location.

The system may provide additional built-in fields where required by the project's initial implementation.

#### 5.1.1 Custom Field Types

The system shall support field types appropriate to the project's requirements, including:

| Type | Description |
| --- | --- |
| Text | Text value |
| Integer | Whole-number value |
| Decimal | Numeric value supporting decimal places |
| Boolean | True/false value |
| Date | Calendar date |
| Enum | One value selected from an Admin-defined list |
| User | Reference to a user account within the system |

Additional field types may be supported in future versions.

#### 5.1.2 Custom Field Configuration

For each custom field, an Office Admin shall be able to configure, where applicable:

- Field name.
- Data type.
- Required or optional status.
- Available Enum values.
- Active or inactive status.
- Checker view permission.
- Checker edit permission.

### 5.2 User Data

The system shall maintain information required for authentication and authorization, including:

- User identifier.
- Name.
- Authentication information.
- Roles.
- Per-user permission overrides.
- Account status.
- Relevant creation and modification timestamps.

### 5.3 Log Data

Logs shall contain, where applicable:

- Event identifier.
- User responsible for the event.
- Event type.
- Affected asset or record.
- Date and time.
- Previous value.
- New value.
- Relevant additional information.

### 5.4 Backup Data

Backups shall contain all data and configuration required for a full system restoration, including:

- Asset records.
- Asset IDs.
- Custom field definitions.
- Custom field values.
- User accounts.
- Roles.
- Permissions and per-user overrides.
- Audit and activity logs.
- Relevant system configuration.

### 5.5 Data Storage

Application data shall be stored in a persistent data store appropriate for the system.

Backup files shall be stored in a configurable backup location that can be accessed independently from the application runtime environment.

For a containerized deployment, the default backup location shall be a directory mounted into the application from the deployment host.

### 5.6 Data Handling

- Required fields shall be validated before records are saved.
- Asset IDs shall not be duplicated.
- An imported asset shall require a Name; fields not supplied shall remain unset unless otherwise required.
- Archived assets shall remain available according to the agreed retention policy.
- Audit records shall be retained according to the agreed retention policy.
- Backup data shall be protected from unauthorized access.
- Data restoration shall preserve relationships between assets, users, custom fields, permissions, and logs.
- Deactivating a custom field shall not automatically destroy existing data associated with that field.

---

## 6. External Interfaces

### 6.1 User Interface

The application shall provide:

- A desktop management interface.
- A mobile asset-checking interface.
- Inventory search and filtering.
- Individual asset pages.
- QR scanning functionality.
- User and permission management for Office Admins.
- Custom field management for Office Admins.
- Audit and activity log views for authorized users on desktop and mobile.
- Export controls for authorized users.
- Import controls for authorized users.
- Backup and restoration controls for authorized users.

The interface shall adapt to the screen size and input method of the device being used.

Access to logs, fields, assets, and other functionality shall be determined by the user's effective permissions rather than the device being used.

### 6.2 External Services

No mandatory external services are currently defined.

Potential external services may be added if required for:

- Authentication.
- File storage.
- Backup storage.
- Other integrations agreed with the client.

Any external service that stores or processes inventory data shall be reviewed and agreed upon before implementation.

### 6.3 Hardware

The system shall support:

- Desktop or laptop computers with a supported web browser.
- Smartphones with a supported web browser and camera for QR scanning.
- QR-code asset stickers or labels.

---

## 7. Constraints & Assumptions

### 7.1 Constraints

- The application shall be browser-based.
- The system shall support both desktop and mobile usage.
- QR scanning shall depend on the capabilities of the user's mobile device and browser.
- The available hosting environment and budget may limit infrastructure and external services.
- The minimum built-in asset fields shall remain simple enough to support initial system operation without requiring custom-field configuration.
- Backup storage shall remain accessible independently of the application runtime environment.

### 7.2 Assumptions

- Each physical asset requiring tracking can be assigned a unique Asset ID.
- The Asset ID will be encoded directly in the asset's QR code.
- Users will have access to a supported web browser.
- Mobile users will have access to a device with a functioning camera when QR scanning is required.
- Office Admins will be responsible for maintaining users, permissions, asset fields, and system-level configuration.
- Office Admins may define additional asset fields beyond the minimum built-in fields.
- Imported inventory requires at minimum a Name; other fields may be left unset.
- Automatic backups are disabled by default.
- The system will prompt an Admin to configure automatic backups during first-time initialization.
- The backup schedule is configurable by an Office Admin when automatic backups are enabled.
- The default backup location is a directory mounted into the application deployment.
- NAS-backed storage may be supported in a later iteration.

---

## 8. Out of Scope

The following are not included in the current project unless separately agreed:

- Automated purchasing or procurement.
- Accounting or financial management.
- Depreciation calculations.
- Automated insurance claims.
- Integration with external ERP or accounting systems.
- Physical printing hardware integration.
- Automatic asset discovery from the office network.
- GPS-based asset tracking.
- Native Android or iOS applications.
- Advanced analytics or reporting.
- Arbitrary modification of the underlying database schema by users.

Future additions may be considered separately.

---

## 9. Acceptance Criteria

The project will be considered complete when:

- [ ] Users can authenticate and access functions according to their effective roles and permissions.
- [ ] Office Admins can create and manage roles.
- [ ] Office Admins can assign roles to users.
- [ ] Office Admins can configure per-user permission overrides.
- [ ] Office Admins can configure which asset fields Checkers can view and edit.
- [ ] Authorized users can create, view, edit, archive, and restore assets as permitted.
- [ ] Each asset receives a unique system-generated UUID as its Asset ID.
- [ ] The Asset ID is encoded in the asset's QR code.
- [ ] A supported mobile device can scan an asset QR code and open the corresponding asset.
- [ ] Asset location is available as a built-in field and supports an unset value.
- [ ] Asset checks and relevant changes are recorded.
- [ ] Asset changes include appropriate audit information.
- [ ] Office Admins can create and configure custom asset fields.
- [ ] Custom fields support the implemented data types required by the project.
- [ ] Custom field values are validated according to their configured types.
- [ ] Authorized users can view relevant logs from supported desktop and mobile devices.
- [ ] Log visibility respects effective user permissions.
- [ ] Users can search, filter, and view inventory records.
- [ ] Custom fields can be used in applicable searches, filters, and exports.
- [ ] Authorized users can import inventory data with at least a Name provided for each asset.
- [ ] Missing optional imported values remain unset.
- [ ] Authorized users can export inventory data in an agreed Excel-compatible format.
- [ ] Export templates can save and apply predefined filters.
- [ ] The system can create manual backups.
- [ ] Automatic backups are disabled by default.
- [ ] The system prompts the Admin to configure automatic backups during first-time initialization.
- [ ] Admins can configure the automatic backup schedule.
- [ ] The system detects missed scheduled backups.
- [ ] A missed scheduled backup is performed on the next application startup.
- [ ] The system avoids duplicate execution of the same scheduled backup.
- [ ] Backups contain all required inventory, user, permission, custom field, and log data.
- [ ] Backup files are stored in the configured backup location.
- [ ] The configured backup location can be accessed outside the application runtime environment.
- [ ] A valid backup can be restored successfully.
- [ ] Backup and restoration activities are appropriately recorded.
- [ ] The application works on the agreed desktop and mobile browsers.
- [ ] The client has reviewed and accepted the completed application.

---

## 10. Open Issues

| ID | Issue | Status |
| --- | --- | --- |
| OI-001 | Confirm any additional built-in fields required beyond Asset ID, Name, Location, Created At, and Updated At | Open |
| OI-002 | Final role definitions and default permissions to be confirmed | Open |
| OI-003 | Final custom field types required for the initial implementation to be confirmed | Open |
| OI-004 | Audit-log retention period to be confirmed | Open |
| OI-005 | Backup retention policy to be confirmed | Open |
| OI-006 | Backup storage deployment configuration to be finalized | Open |
| OI-007 | NAS backup support to be evaluated as a lower-priority feature | Open |

---

## 11. Change History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-08-15 | Initial requirements |
| 0.2 | 2026-08-17 | Defined permission matching. |
| 0.3 | 2026-08-21 | Expanded authorization requirements. |
| 0.4 | 2025-08-25 | Refactored feature request codes. |
| 0.5 | 2025-08-25 | Update requirement priorities per client. |

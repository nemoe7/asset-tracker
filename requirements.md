# Inventory Management

**Client:** The Birth-Giver
**Developer:** nemoe7
**Version:** 0.3
**Last Updated:** 2026-08-21

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

# 2. System Overview

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

# 3. Functional Requirements

## 3.1 Authentication and Access Control

The system shall authenticate users and enforce their assigned permissions.

- **FR-001:** The system shall allow users to log in using their assigned credentials.
- **FR-002:** The system shall provide a mechanism for users to log out.
- **FR-003:** The system shall restrict functionality according to the user's assigned roles and permissions.
- **FR-004:** The system shall restrict access to asset information according to the user's permissions.
- **FR-005:** The system shall enforce the same permission rules on supported desktop and mobile interfaces.
- **FR-006:** The system shall prevent unauthenticated users from accessing protected functionality.

### Permission Matching

Permissions shall support wildcard matching and precedence rules.

- **FR-003.1:** The system shall support exact permission grants.
- **FR-003.2:** The system shall support namespace wildcard grants using the `namespace.*` format.
- **FR-003.3:** A namespace wildcard grant shall grant access to all concrete permissions within that namespace.
- **FR-003.4:** The system shall support the global wildcard grant `*`.
- **FR-003.5:** A global wildcard grant shall grant access to all concrete permissions.
- **FR-003.6:** Wildcard grants shall automatically apply to newly created concrete permissions that match the wildcard.
- **FR-003.7:** Direct user permission decisions shall take precedence over permissions inherited from roles.
- **FR-003.8:** When multiple permissions from the same source match a requested permission, the most specific matching permission shall take precedence.
- **FR-003.9:** When conflicting role permissions have equal specificity, a deny decision shall take precedence.
- **FR-003.10:** Permission changes shall take effect on subsequent authorization checks without requiring the affected user to authenticate again.
- **FR-003.11:** Permission checks shall request concrete permissions using the `namespace.operation` format.

## 3.2 User Management and Permissions

Office Admins shall be able to manage users and configure permissions.

- **FR-007:** Office Admins shall be able to create user accounts.
- **FR-008:** Office Admins shall be able to modify user accounts.
- **FR-009:** Office Admins shall be able to deactivate user accounts.
- **FR-010:** Office Admins shall be able to create and manage roles.
- **FR-011:** Office Admins shall be able to assign roles to users.
- **FR-012:** Office Admins shall be able to configure permissions for roles.
- **FR-013:** Office Admins shall be able to configure per-user permission overrides.
- **FR-014:** Per-user permissions shall be able to override the permissions inherited from the user's roles.
- **FR-015:** Office Admins shall be able to configure which asset fields Checkers can view.
- **FR-016:** Office Admins shall be able to configure which asset fields Checkers can edit.
- **FR-017:** Checkers shall not be able to modify their own permissions.
- **FR-018:** Office Admins shall be able to configure which users or roles can view audit and activity logs.
- **FR-019:** The system shall record relevant user, role, and permission changes in the audit log.

## 3.3 Asset Management

The system shall maintain records for office assets.

- **FR-020:** Authorized users shall be able to create an asset record.
- **FR-021:** Authorized users shall be able to view asset records.
- **FR-022:** Authorized users shall be able to edit asset records according to their permissions.
- **FR-023:** Authorized users with the appropriate permissions shall be able to archive asset records.
- **FR-024:** The system shall automatically generate a unique Asset ID for each new asset.
- **FR-025:** The Asset ID shall be a UUID.
- **FR-026:** The system shall validate required asset information before saving an asset.
- **FR-027:** The system shall prevent duplicate Asset IDs.
- **FR-028:** Archived assets shall remain available to authorized users for historical reference.
- **FR-029:** Archived assets shall be distinguishable from active assets.
- **FR-030:** The system shall not permanently delete an asset through normal inventory management functions.
- **FR-031:** Authorized users shall be able to restore an archived asset to an active state.
- **FR-032:** The system shall retain relevant asset information required for inventory and insurance purposes.

## 3.4 Configurable Asset Fields

The system shall provide a minimum set of built-in asset fields and allow Office Admins to define additional custom fields.

- **FR-033:** The system shall provide the minimum built-in asset fields defined in Section 5.1.
- **FR-034:** Office Admins shall be able to create custom asset fields.
- **FR-035:** Office Admins shall be able to specify a name for each custom field.
- **FR-036:** Office Admins shall be able to specify the data type of each custom field.
- **FR-037:** The system shall support appropriate field types for the project's requirements, including at minimum:
  - Text
  - Integer
  - Decimal
  - Boolean
  - Date
  - Enum
  - User
- **FR-038:** Office Admins shall be able to define the available values for an Enum field.
- **FR-039:** A User field shall reference a user account within the system.
- **FR-040:** Office Admins shall be able to specify whether a custom field is required.
- **FR-041:** Office Admins shall be able to modify custom field configuration subject to data integrity constraints.
- **FR-042:** Office Admins shall be able to deactivate a custom field.
- **FR-043:** Deactivating a custom field shall not automatically remove existing values associated with that field.
- **FR-044:** Custom field values shall be validated according to their configured data type.
- **FR-045:** Custom fields shall be available for viewing and editing according to user permissions.
- **FR-046:** Custom fields shall be available for searching, filtering, and exporting where applicable.
- **FR-047:** Changes to custom field definitions shall be recorded in the audit log.

## 3.5 Asset Identification and QR Codes

Each asset shall be identified using its Asset ID, which is encoded in its QR code.

- **FR-048:** The system shall associate each asset with a unique Asset ID.
- **FR-049:** The Asset ID shall be encoded in the asset's QR code.
- **FR-050:** The Asset ID shall uniquely identify its associated asset.
- **FR-051:** The system shall support scanning asset QR codes using supported mobile devices.
- **FR-052:** Scanning an asset QR code shall open the corresponding asset record.
- **FR-053:** The system shall provide the information required to create an asset identification sticker.
- **FR-054:** The QR code shall contain the Asset ID and shall not need to contain the asset's complete information.

## 3.6 Asset Checking and Scanning

The system shall support physical inventory checking through QR scanning.

- **FR-055:** A Checker shall be able to scan an asset QR code using a supported mobile device.
- **FR-056:** The system shall identify the asset from the scanned Asset ID.
- **FR-057:** The system shall record the scan event.
- **FR-058:** The system shall record the user who performed the scan.
- **FR-059:** The system shall record the date and time of the scan.
- **FR-060:** The system shall indicate when a scanned Asset ID does not correspond to an existing asset.
- **FR-061:** A Checker shall be able to update permitted asset information after scanning.
- **FR-062:** The system shall record changes resulting from an asset check.
- **FR-063:** Archived assets shall be handled according to their status and the user's permissions when scanned.

## 3.7 Search, Filtering, and Inventory Views

The system shall provide database-like inventory views.

- **FR-064:** Users shall be able to search for assets.
- **FR-065:** Users shall be able to filter assets using available asset fields.
- **FR-066:** Users shall be able to sort asset results using available fields.
- **FR-067:** The system shall display asset information in a tabular or equivalent inventory view.
- **FR-068:** The system shall allow users to open an individual asset from an inventory view.
- **FR-069:** Applied filters shall affect the displayed results and filtered exports where applicable.
- **FR-070:** Custom fields shall be available as search and filter criteria where applicable.

## 3.8 Audit and Activity Logs

The system shall maintain an audit trail of relevant system activity.

- **FR-071:** The system shall record asset creation events.
- **FR-072:** The system shall record asset modification events.
- **FR-073:** The system shall record asset archival and restoration events.
- **FR-074:** The system shall record asset QR scan events.
- **FR-075:** The system shall record custom field creation, modification, and deactivation events.
- **FR-076:** The system shall record user, role, and permission changes.
- **FR-077:** The system shall record backup and restoration events.
- **FR-078:** The system shall record the user responsible for each logged event.
- **FR-079:** The system shall record the date and time of each logged event.
- **FR-080:** For applicable asset changes, the system shall record the affected field and its previous and new values.
- **FR-081:** Authorized users shall be able to view relevant audit and activity logs from supported desktop and mobile devices.
- **FR-082:** The system shall restrict log visibility according to the user's permissions.
- **FR-083:** Audit logs shall not be editable through normal inventory management functions.

## 3.9 Export

The system shall allow inventory information to be exported.

- **FR-084:** Authorized users shall be able to export inventory data.
- **FR-085:** The system shall provide an Excel-compatible export format.
- **FR-086:** Users shall be able to select which fields are included in an export where supported.
- **FR-087:** Users shall be able to export filtered inventory results.
- **FR-088:** Authorized users shall be able to create saved export templates.
- **FR-089:** An export template shall consist of a predefined set of filters and applicable export field selections.
- **FR-090:** Users shall be able to apply a saved export template before generating an export.
- **FR-091:** Export templates shall support configured custom fields.
- **FR-092:** Exported data shall reflect the information available to the user generating the export.

## 3.10 Import

The system shall support importing existing inventory data.

- **FR-093:** Authorized users shall be able to import asset records.
- **FR-094:** An import shall require, at minimum, an Asset Name for each imported asset.
- **FR-095:** The system shall automatically generate an Asset ID for imported assets where one is not provided.
- **FR-096:** Optional fields not supplied during import shall remain unset.
- **FR-097:** The system shall validate imported values against the corresponding field types and requirements.
- **FR-098:** The system shall report invalid or rejected records without corrupting existing inventory data.
- **FR-099:** Import operations shall be recorded in the audit log.

## 3.11 Backup and Restore

The system shall support scheduled and manual backups and full-system restoration.

- **FR-100:** Automatic backups shall be disabled by default.
- **FR-101:** During first-time system initialization, the system shall prompt the Admin to configure automatic backups.
- **FR-102:** Office Admins shall be able to enable or disable automatic backups.
- **FR-103:** Office Admins shall be able to configure the automatic backup schedule.
- **FR-104:** The default proposed schedule shall be once per week on Sunday at 03:00 when automatic backups are enabled.
- **FR-105:** The system shall detect when a scheduled backup was missed because the application was not running at the scheduled time.
- **FR-106:** If a scheduled backup was missed, the system shall perform the pending backup when the application next starts.
- **FR-107:** The system shall avoid creating duplicate backups for the same scheduled backup period.
- **FR-108:** The system shall record the scheduled backup time and the actual backup time.
- **FR-109:** A system backup shall include:
  - Asset records.
  - User accounts.
  - Roles and permissions.
  - Custom field definitions and configuration.
  - Custom field values.
  - Audit and activity logs.
  - Relevant system configuration required for restoration.
- **FR-110:** Authorized users shall be able to create a system backup manually.
- **FR-111:** Authorized users shall be able to restore the system from a valid backup.
- **FR-112:** The system shall warn users before a restoration that may overwrite existing data.
- **FR-113:** The system shall record backup and restoration events in the audit log.
- **FR-114:** The system shall provide backup status and confirmation information.
- **FR-115:** The system shall maintain backup files in a configurable storage location.
- **FR-116:** The default backup location shall be a directory mounted into the application deployment.
- **FR-117:** The backup location shall be configurable independently of the application runtime.
- **FR-118:** The system should support externally hosted backup locations such as NAS storage where practical.

---

# 4. Non-Functional Requirements

## 4.1 Performance

- **NFR-001:** Normal inventory operations shall respond within a reasonable time under the expected number of users and assets.
- **NFR-002:** Asset searches and filtering shall not require the user to manually reload the application.
- **NFR-003:** QR scanning shall open the corresponding asset record without unnecessary intermediate steps.

## 4.2 Usability

- **NFR-004:** The application shall be usable through a standard web browser.
- **NFR-005:** The interface shall provide a desktop-oriented management experience.
- **NFR-006:** The interface shall provide a mobile-oriented experience for asset checking and QR scanning.
- **NFR-007:** Common asset operations shall require minimal navigation.
- **NFR-008:** Archival and restoration operations shall require appropriate confirmation.
- **NFR-009:** Backup configuration shall clearly indicate whether automatic backups are enabled and the next scheduled backup time.

## 4.3 Security

- **NFR-010:** Protected system functions shall require authentication.
- **NFR-011:** The system shall enforce role-based and per-user access control.
- **NFR-012:** Users shall only be able to access information and functions permitted by their effective permissions.
- **NFR-013:** Authentication credentials shall not be stored in plaintext.
- **NFR-014:** Audit logs shall be protected against modification by unauthorized users.
- **NFR-015:** Backup and restore functions shall be restricted to authorized users.
- **NFR-016:** Backup files shall be protected from unauthorized access.
- **NFR-017:** Custom field configuration shall not bypass the system's fundamental data integrity or security controls.

## 4.4 Compatibility

- **NFR-018:** The application shall support current versions of commonly used desktop web browsers.
- **NFR-019:** The application shall support modern mobile browsers on supported smartphones.
- **NFR-020:** QR scanning shall work with supported mobile device cameras or browser-based scanning functionality.

## 4.5 Reliability and Recovery

- **NFR-021:** The system shall handle invalid user input without corrupting existing inventory data.
- **NFR-022:** Failed operations shall provide an appropriate error message.
- **NFR-023:** The system shall maintain data integrity when creating or modifying records.
- **NFR-024:** A valid backup shall be sufficient to restore the required application data.
- **NFR-025:** The system shall not report a backup as successful unless the backup operation has completed successfully.
- **NFR-026:** The system shall retain sufficient information to determine when the most recent successful backup occurred.
- **NFR-027:** A missed scheduled backup shall be recoverable on the next application startup.

---

# 5. Data Requirements

## 5.1 Minimum Asset Data

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

### 5.1.1 Custom Field Types

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

### 5.1.2 Custom Field Configuration

For each custom field, an Office Admin shall be able to configure, where applicable:

- Field name.
- Data type.
- Required or optional status.
- Available Enum values.
- Active or inactive status.
- Checker view permission.
- Checker edit permission.

## 5.2 User Data

The system shall maintain information required for authentication and authorization, including:

- User identifier.
- Name.
- Authentication information.
- Roles.
- Per-user permission overrides.
- Account status.
- Relevant creation and modification timestamps.

## 5.3 Log Data

Logs shall contain, where applicable:

- Event identifier.
- User responsible for the event.
- Event type.
- Affected asset or record.
- Date and time.
- Previous value.
- New value.
- Relevant additional information.

## 5.4 Backup Data

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

## 5.5 Data Storage

Application data shall be stored in a persistent data store appropriate for the system.

Backup files shall be stored in a configurable backup location that can be accessed independently from the application runtime environment.

For a containerized deployment, the default backup location shall be a directory mounted into the application from the deployment host.

## 5.6 Data Handling

- Required fields shall be validated before records are saved.
- Asset IDs shall not be duplicated.
- An imported asset shall require a Name; fields not supplied shall remain unset unless otherwise required.
- Archived assets shall remain available according to the agreed retention policy.
- Audit records shall be retained according to the agreed retention policy.
- Backup data shall be protected from unauthorized access.
- Data restoration shall preserve relationships between assets, users, custom fields, permissions, and logs.
- Deactivating a custom field shall not automatically destroy existing data associated with that field.

---

# 6. External Interfaces

## 6.1 User Interface

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

## 6.2 External Services

No mandatory external services are currently defined.

Potential external services may be added if required for:

- Authentication.
- File storage.
- Backup storage.
- Other integrations agreed with the client.

Any external service that stores or processes inventory data shall be reviewed and agreed upon before implementation.

## 6.3 Hardware

The system shall support:

- Desktop or laptop computers with a supported web browser.
- Smartphones with a supported web browser and camera for QR scanning.
- QR-code asset stickers or labels.

---

# 7. Constraints & Assumptions

## 7.1 Constraints

- The application shall be browser-based.
- The system shall support both desktop and mobile usage.
- QR scanning shall depend on the capabilities of the user's mobile device and browser.
- The available hosting environment and budget may limit infrastructure and external services.
- The minimum built-in asset fields shall remain simple enough to support initial system operation without requiring custom-field configuration.
- Backup storage shall remain accessible independently of the application runtime environment.

## 7.2 Assumptions

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

# 8. Out of Scope

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

# 9. Acceptance Criteria

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

# 10. Open Issues

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

# 11. Change History

| Version | Date | Changes |
| --- | --- | --- |
| 0.1 | 2026-08-15 | Initial requirements |
| 0.2 | 2026-08-17 | Defined permission matching. |
| 0.3 | 2026-08-21 | Expanded authorization requirements. |

# Data Service Conventions

## 1. Purpose

This document defines conventions for the data services in `app/services/data/`.

Data services are responsible for:

- Reading and modifying persistent application data.
- Enforcing data-level validation and integrity rules.
- Managing transactions for their operations.
- Creating required audit records for mutations.
- Remaining independent of Flask and HTTP concerns.

The database schema is defined separately in `database/schema.sql`.

---

## 2. Service Boundaries

Data services shall:

- Operate on persistent application data.
- Contain domain/data validation required to safely perform their operations.
- Use database constraints as the final integrity authority.
- Remain independent of Flask, HTTP requests, responses, sessions, and templates.
- Use other data services when a legitimate data lookup or validation is required.

Data services shall not:

- Perform HTTP redirects.
- Return Flask responses.
- Inspect request/session state directly.
- Make authorization decisions.
- Format user-facing error messages.

Authorization decisions belong to the authorization layer.

---

## 3. Database Schema Boundary

`database/schema.sql` defines the database structure.

`app/services/data/` implements operations against that structure.

Data services shall not dynamically modify the database schema during normal operation.

Schema changes shall be made through the project's schema/migration mechanism.

---

## 4. Database Connections

Data services shall use the application's database connection context.

A connection context shall provide the current database connection to data services and nested service calls.

When no connection context exists, the operation may establish and own a connection.

When a connection context exists:

- Data services shall use the contextual connection.
- Data services shall not create a separate connection.
- Data services shall not close the contextual connection.
- Data services shall not commit or roll back the contextual connection unless they own the transaction.

The connection context owns the connection lifecycle and transaction when it establishes the connection.

This allows multiple service operations and nested service calls to participate in one transaction without explicitly passing a connection through every service call.

---

## 5. Transaction Ownership

A normal public mutating service operation owns its transaction.

The normal sequence is:

1. Open a database connection.
2. Perform validation.
3. Perform the mutation.
4. Create required audit records using the same connection.
5. Commit.
6. Close the connection.

If the operation fails, the transaction is rolled back.

When an existing connection is supplied, transaction ownership belongs to the caller.

---

## 6. Atomicity

A mutation and its required audit records shall be atomic.

If the mutation succeeds but the required audit record cannot be created, the entire operation shall be rolled back.

If the mutation fails, its audit record shall not remain in the database.

This prevents states such as:

- A change occurring without an audit record.
- An audit record existing for a change that was rolled back.

The same principle applies to multi-step operations performed within one transaction.

---

## 7. Nested Service Calls

A data service may call another data service when doing so represents a legitimate data operation, particularly:

- Looking up a related record.
- Validating that a related record exists.
- Obtaining data required to perform the operation.

Nested data-service calls shall automatically use the caller's database connection context.

A nested service call shall not unnecessarily create a second connection or transaction.

Data services should not be chained arbitrarily merely to avoid placing straightforward data logic in the appropriate service.

---

## 8. Reads

Single-record lookup functions shall return:

- The requested record when it exists.
- `None` when it does not exist.

Example:

```python
location = get_location(location_id)

if location is None:
  ...
```

Absence during a read is therefore a normal result and is not an exception.

---

## 9. Mutations and Missing Records

Mutating operations require their target record to exist.

If the target does not exist, the service shall raise the specific `NotFoundError` associated with that entity.

Example:

```python
update_location(
  "does-not-exist",
  name="Storage",
)
# → LocationNotFoundError
```

This applies to operations such as:

- Update.
- Archive.
- Restore.
- Permanent deletion.

The distinction is intentional:

- Reads use `None` for absence.
- Mutations raise a specific not-found exception because the requested operation cannot be performed.

---

## 10. Collection Reads

Collection functions shall return a list.

When no records match, they shall return an empty list rather than `None`.

Example:

```python
locations = get_locations(...)

# No matching records:
locations == []
```

---

## 11. Default Ordering

Collection queries shall have deterministic default ordering.

Each service may choose the most appropriate primary ordering for its entity.

Where multiple records can have the same primary ordering value, a stable unique identifier should be used as a tie-breaker where appropriate.

Examples include:

- Locations ordered by ID.
- Users ordered by username.
- Inventory ordered by name and then ID.

Callers should not rely on unspecified database ordering.

---

## 12. Pagination

The current data-service API returns the complete matching collection.

Pagination is not currently part of the data-service contract.

Pagination may be introduced later as an explicit API feature rather than being implicitly added to existing collection functions.

---

## 13. Filtering

Filtering belongs in the data service responsible for the corresponding domain.

For example, inventory filtering may include:

- Search.
- Location.
- Archived status.
- Other supported inventory fields.

Filtering shall use explicitly supported parameters.

Unknown or unsupported filter parameters shall not silently alter the query.

A generic dynamic SQL filtering mechanism shall not be introduced unless explicitly required.

---

## 14. Input Normalization

Data services shall validate string input using its meaningful content.

Whitespace-only strings shall be considered empty where the field is required.

Services shall not implicitly normalize stored input unless the service explicitly defines that behavior.

In particular, services shall not automatically:

- Strip leading/trailing whitespace from stored values.
- Convert values to lowercase.
- Change capitalization.
- Convert empty strings to `None`.

Normalization requirements should be explicit and field-specific.

---

## 15. Nullable Values

`None` represents an explicitly unset nullable value.

An empty string is not automatically converted to `None`.

For example, a nullable foreign key may legitimately receive:

```python
location_id=None
```

while a required text field receiving:

```python
name=""
```

shall fail its required-field validation.

---

## 16. Partial Updates

Partial update functions shall distinguish between:

- A field being omitted from the update.
- A field explicitly being set to `None`.

The internal `_UNSET` sentinel shall represent an omitted argument.

`None` shall represent an explicit NULL/unset value where the field permits it.

Example:

```python
update_item(
  item_id,
  name=_UNSET,
  location_id=None,
)
```

means:

- Leave `name` unchanged.
- Explicitly clear `location_id`.

`_UNSET` is an internal implementation sentinel and should not be persisted or exposed as application data.

---

## 17. No-Op Mutations

A mutation that produces no actual state change shall succeed without modifying the record.

A no-op mutation shall:

- Return the operation's normal success result.
- Not change `updated_at`.
- Not create an audit record.
- Not perform an unnecessary database mutation.

This applies to idempotent operations such as archive and restore.

For example:

```python
archive_custom_field(already_archived_id)
# → False
```

indicates that no state change occurred.

---

## 18. Return Values

Service functions shall return the smallest useful domain result required by their caller.

Return types are operation-specific rather than universally standardized.

Examples:

- Create operations return the newly created entity ID.
- Update operations may return a success indicator.
- Archive/restore operations may return a success indicator.
- Operations producing meaningful result data may return that data.

Services shall not return Flask responses, HTTP status codes, redirects, or other presentation-layer values.

---

## 19. Entity Creation

Create operations shall normally return the newly created entity's identifier.

Example:

```python
location_id = create_location(
  name="Storage",
)
```

The data service is responsible for generating IDs according to the entity's schema and established ID format.

Callers shall not normally supply entity IDs unless the specific service explicitly supports it.

---

## 20. IDs

ID generation belongs to the data layer.

Each entity shall use the ID type defined by its database schema.

For UUID-based entities, the service shall generate a valid UUID.

For database-generated integer IDs, the database shall generate the identifier.

IDs shall be unique and shall not be silently replaced when a conflict occurs.

---

## 21. Timestamps

Database timestamps shall be generated by the database using the established timestamp mechanism.

The current application uses SQLite UTC timestamps.

The following conventions apply:

- `created_at` is immutable.
- Where an entity has an `updated_at` column, it changes when persisted data actually changes.
- No-op operations shall not change `updated_at`.
- Where an entity has an `updated_at` column, archival and restoration count as state changes and therefore update `updated_at`.

---

## 22. Validation

Services shall validate input before attempting the relevant mutation.

Validation shall cover:

- Required fields.
- Supported values.
- Data types.
- Related-record requirements.
- Domain-specific constraints.

Validation failures shall use the existing specific service/domain exceptions.

Generic `ValueError` or `Exception` shall not be used where an established specific exception exists.

---

## 23. Exceptions

Expected domain failures shall use specific service exceptions.

Examples include:

- `LocationNotFoundError`.
- `ItemNotFoundError`.
- Entity-specific validation errors.
- Entity-specific conflict errors.
- Entity-specific archived-state errors.

Unexpected programming, database, or infrastructure exceptions shall propagate rather than being converted into generic domain errors.

This preserves the distinction between:

- An expected failure caused by the requested operation.
- An unexpected application/server failure.

The Flask layer is responsible for translating exceptions into appropriate HTTP behavior.

---

## 24. Database Integrity

Data integrity shall be enforced at both the service and database levels where practical.

The service layer should perform validation so that callers receive meaningful domain-specific errors.

The database remains the final authority for constraints such as:

- Primary keys.
- Unique constraints.
- Foreign keys.
- Not-null constraints.

Service validation shall not be treated as a replacement for database constraints.

---

## 25. Foreign Keys

Foreign-key enforcement shall remain enabled for database connections.

Services should validate referenced entities when doing so allows them to provide an appropriate domain-specific error.

The database shall still enforce the foreign-key relationship.

For example, inventory operations that reference a location may first look up the location using the same transaction connection.

---

## 26. Archival

Archival is a state transition and is distinct from permanent deletion.

Entities supporting archival shall provide explicit archive and restore operations.

Archiving shall preserve the record and its historical information.

Archived records shall remain available for authorized historical access.

Archiving an already archived entity shall raise the entity's specific archived-state exception.

Restoring an active entity shall raise the entity's specific not-archived-state exception.

---

## 27. Permanent Deletion

Permanent deletion shall only be implemented for entities explicitly designated as deletable.

If an entity supports archival, its normal lifecycle shall be:

```text
active → archived → restored
```

rather than:

```text
active → deleted
```

Locations are an example of an entity that may be permanently deleted.

Inventory assets and other archival entities shall not be permanently deleted through normal data-service operations.

---

## 28. Archived Records

Normal collection and single-record reads shall exclude archived records unless the caller explicitly requests archived records.

Archived records shall generally be read-only.

Operations that modify an archived entity shall fail with the entity's appropriate archived-state exception unless the operation is specifically intended to restore or otherwise manage the archived state.

An archived record must normally be restored before ordinary modification.

Archiving an already archived record and restoring an already active record shall fail with their respective entity-specific state exceptions.

---

## 29. Audit Logging

Mutating data services are responsible for creating required audit records.

Audit records shall be created using the same database connection and transaction as the mutation.

Audit records shall identify the appropriate actor according to the application's established audit context.

No-op operations shall not create audit records.

When a persisted value is created, changed, or removed, the audit record shall describe the state transition.

For value changes, audit details shall include both the previous value and the new value.

For creation:

```text
old_value: null
new_value: <created value>
````

For updates:

```text
old_value: <previous value>
new_value: <new value>
```

For removal:

```text
old_value: <previous value>
new_value: null
```

Replacing a value with the same value is a no-op and shall not create an audit record.

Audit records shall not be directly editable through ordinary data-service operations.

---

## 30. Audit Actor Context

User-attributable mutations requiring audit logging shall execute within an authenticated actor context.

The audit service shall obtain the actor from the application's established current-user context.

The audit service shall not silently create anonymous audit records when an actor is required.

If the required actor context is unavailable, the operation shall fail rather than producing an unattributed audit record.

---

## 31. Audit Details

Structured audit details shall be represented as application-level data structures.

JSON serialization shall occur only at the persistence boundary.

When audit records are read, their stored JSON details shall be deserialized back into application-level data.

Data services and callers should therefore work with structured details rather than raw JSON strings.

---

## 32. Audit Records Are Append-Only

Audit records shall be append-only.

Normal data services shall provide:

- Creation of audit records.
- Retrieval of audit records.

They shall not provide normal update or delete operations for audit records.

---

## 33. Authorization

Data services shall not independently implement the application's permission system.

Authorization decisions belong to the authorization layer.

Data services may still enforce domain/data integrity rules that are independent of authorization.

For example:

- Authorization determines whether a user may update an inventory item.
- The inventory data service determines whether the item exists, whether it is archived, and whether the supplied data is valid.

This keeps permission logic centralized and prevents duplication across data services.

---

## 34. Relationship Services

Many-to-many relationship tables that represent independently manipulated application relationships shall have dedicated data services.

Examples include:

- User ↔ Role.
- Role ↔ Permission.
- User ↔ Permission.

Callers shall use the appropriate relationship service rather than directly modifying relationship tables.

---

## 35. Supporting-Record Deletion

Archival applies to domain entities whose historical identity must be retained.

Supporting records may be permanently deleted when their absence represents the correct application state.

Examples include:

- Sparse custom-field value records.
- Relationship/junction records.

Permanent deletion of such records does not imply that the associated domain entity itself should be permanently deleted.

---

## 36. Custom Field Types

Custom-field values shall be validated according to their configured field type.

Supported types include:

- Text.
- Integer.
- Decimal.
- Boolean.
- Date.
- Enum.
- User.

Validation shall occur before persistence.

SQLite's flexible typing shall not be relied upon to enforce application-level custom-field types.

---

## 37. Custom Field Serialization

Data services shall convert custom-field values between their application representation and database representation.

Database serialization shall not leak into callers.

For example, boolean custom-field values may be stored using the database representation required by the schema while callers continue to use Python boolean values.

The serialization rules shall be determined by the configured custom-field type.

---

## 38. Custom Field Value Absence

Sparse custom-field values represent whether an inventory item has a value for a particular custom field.

For such fields:

```python
set_custom_field_value(
  item_id,
  field_id,
  None,
)
```

shall represent absence of a stored value.

The value record shall be removed rather than storing a database NULL value.

This convention applies specifically to sparse custom-field value records and does not override the general nullable-column convention.

---

## 39. Custom Field References

Custom field types that reference other entities shall validate that the referenced entity exists and is in an appropriate state.

For example, a `User` custom field shall reference an existing active user.

The reference shall be validated using the same transaction connection when the operation is already participating in a transaction.

---

## 40. SQL

SQL for domain operations shall remain directly within the relevant data service.

A repository/DAO abstraction is not currently required.

The current architecture is:

```text
route
  ↓
service
  ↓
data service
  ↓
SQLite
```

rather than introducing an additional repository layer.

Shared database connection utilities may remain in the data/database infrastructure.

---

## 41. Bulk Operations

No generic bulk-operation convention is currently established.

Bulk import is a separate functional requirement and shall define its own transaction and error-handling behavior when implemented.

A bulk operation shall not be assumed to have per-record or all-or-nothing semantics until explicitly defined.

---

## 42. Service Independence from Flask

Data services shall be usable without Flask.

They shall not directly depend on:

- `flask.request`.
- `flask.session`.
- Flask route objects.
- HTTP response objects.
- Templates.
- HTTP status codes.

This allows data services to be tested directly with pytest and reused by routes, background operations, imports, backups, or other application components.

---

## 43. Testing Expectations

Data-service tests shall test service behavior independently of Flask routes and UI behavior.

Tests should cover, where applicable:

- Successful creation.
- Successful retrieval.
- Missing-record retrieval.
- Validation failures.
- Duplicate/conflict failures.
- Updates.
- No-op updates.
- Archival.
- Restoration.
- Permanent deletion where supported.
- Archived-record restrictions.
- Foreign-key behavior.
- Audit creation.
- Audit/mutation transaction atomicity.
- Rollback on failure.
- Connection-context behavior.
- Collection ordering.
- Filtering.
- Serialization and deserialization.
- Custom-field type validation.
- Custom-field value absence.
- Permission-independent data behavior.

Route tests shall separately verify that the Flask layer correctly translates service outcomes into HTTP behavior.

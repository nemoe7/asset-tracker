# Authorization Conventions

## 1. Purpose

This document defines conventions for authorization within the application.

Authorization determines whether an authenticated user is permitted to perform a specific operation.

Authorization is independent of Flask and HTTP concerns.

The authorization layer shall:

- Determine whether a user has a requested permission.
- Resolve permissions inherited from roles.
- Resolve per-user permission overrides.
- Apply permission specificity and precedence rules.
- Support wildcard permission grants.

The authorization layer shall not:

- Handle HTTP requests or responses.
- Read or modify Flask sessions.
- Perform redirects.
- Decide how an authorization failure is presented to the user.
- Implement domain-specific data validation.

---

## 2. Permission Check API

The fundamental authorization operation shall be:

```python
has_permission(user_id, permission_name) -> bool
````

The function shall:

- Receive an explicit user ID.
- Receive one concrete permission to check.
- Return `True` when the permission is granted.
- Return `False` when the permission is denied.

The authorization layer shall not require Flask to perform a permission check.

---

## 3. Concrete Permission Requests

Permission checks shall request a concrete permission using the format:

```text
namespace.operation
```

Examples:

```text
inventory.read
inventory.update
users.create
users.delete
field.12.read
field.34.update
```

A wildcard grant may be stored in the permission system, but wildcard strings shall not be supplied as the requested permission to `has_permission()`.

For example:

```text
has_permission(user_id, "inventory.read")  → valid
has_permission(user_id, "field.12.read")   → valid
has_permission(user_id, "inventory.*")     → invalid request
has_permission(user_id, "*")               → invalid request
```

The application shall define and use concrete permissions when performing authorization checks.

---

## 4. Permission Grants

Permissions assigned to users or roles represent grants.

A grant may be either:

- An exact permission.
- A namespace wildcard.
- The global wildcard.

Examples:

```text
inventory.read
inventory.*
*
field.*
```

Wildcard grants shall not be expanded into individual permission records.

They shall be evaluated dynamically against the requested concrete permission.

---

## 5. Wildcard Grants

A permission ending in `.*` grants all concrete operations within that namespace.

For example:

```text
inventory.*
```

matches:

```text
inventory.read
inventory.create
inventory.update
inventory.delete
```

A global wildcard:

```text
*
```

matches every concrete permission.

For example:

```text
*
```

matches:

```text
inventory.read
users.create
field.12.read
field.34.delete
```

---

## 6. Dynamic Wildcard Matching

Wildcard grants shall be evaluated at authorization-check time.

They shall not be expanded when the grant is assigned.

For example, if a user has:

```text
field.*
```

and the application later creates a new field with ID `57`, the grant automatically applies to:

```text
field.57.read
field.57.update
field.57.delete
```

No additional permission records shall be created for field `57`.

This also applies to the global wildcard:

```text
*
```

New concrete permissions automatically match an existing global wildcard grant.

---

## 7. Permission Naming

Permissions shall use:

```text
namespace.operation
```

where the namespace identifies the resource and the operation identifies the action.

Examples:

```text
inventory.read
inventory.update
users.create
users.archive
locations.delete
```

Operations involving a specific custom field shall include the field identifier in the permission namespace.

Examples:

```text
field.12.read
field.12.update
field.34.read
field.34.delete
```

This allows permissions to be assigned to individual custom fields as well as through wildcard grants such as:

```text
field.*
```

---

## 8. Permission Specificity

When multiple grants from the same permission source match a requested permission, the most specific matching grant takes precedence.

For example, for:

```text
inventory.update
```

the specificity order is:

```text
inventory.update
inventory.*
*
```

For:

```text
field.12.read
```

the applicable specificity hierarchy is determined from the permission structure, with the exact permission being more specific than broader wildcard grants.

The general rule is:

> A more specific matching grant overrides a less specific matching grant from the same source.

---

## 9. User vs Role Precedence

Direct user permissions take precedence over permissions inherited from roles.

The precedence order is:

```text
user permissions
    ↓
role permissions
    ↓
deny
```

This means a user's direct permission decision is evaluated before any permission inherited from their roles.

Example:

```text
Role:
inventory.* → allow

User:
inventory.update → deny
```

Request:

```text
inventory.update
```

Result:

```text
deny
```

The direct user decision overrides the role decision.

---

## 10. User Permission Specificity

Specificity is evaluated within the user's direct permissions before falling back to roles.

For example:

```text
User:
inventory.*       → allow
inventory.update   → deny
```

Request:

```text
inventory.update
```

Result:

```text
deny
```

The exact user permission is more specific than the user's wildcard grant.

Conversely:

```text
User:
inventory.*       → allow
```

allows:

```text
inventory.read
inventory.update
inventory.delete
```

unless a more-specific user grant overrides the wildcard.

---

## 11. Role Permission Specificity

The same specificity rules apply when evaluating role permissions.

For example:

```text
Role:
inventory.*       → allow
inventory.delete   → deny
```

Request:

```text
inventory.delete
```

Result:

```text
deny
```

The exact permission is more specific than the namespace wildcard.

---

## 12. Multiple Roles

A user may have multiple roles.

Role permissions shall be evaluated together according to permission specificity.

A more-specific matching role permission takes precedence over a less-specific matching role permission.

If multiple role grants at the same specificity level produce conflicting decisions, denial shall take precedence.

Example:

```text
Role A:
inventory.* → allow

Role B:
inventory.delete → deny
```

Request:

```text
inventory.delete
```

Result:

```text
deny
```

because `inventory.delete` is more specific than `inventory.*`.

---

## 13. Direct User Conflicts

The database shall prevent duplicate direct permission assignments that would create the same user/permission relationship.

For example, the following should not be representable as duplicate rows:

```text
user 1 → inventory.read
user 1 → inventory.read
```

The authorization layer therefore does not need arbitrary duplicate-row resolution for identical user/permission assignments.

Where explicit allow/deny state is represented separately, the defined permission precedence rules shall determine the effective result.

---

## 14. Undefined Requested Permissions

Application code shall use permissions defined by the application.

If authorization is asked to check an undefined permission, the authorization layer shall raise an appropriate programming/configuration error rather than silently treating the permission as denied.

For example:

```python
has_permission(
  user_id,
  "inventory.fuckshit",
)
```

should not silently become:

```text
False
```

if `inventory.fuckshit` is not a defined application permission.

---

## 15. Dynamic Permissions

Permissions do not need to be pre-expanded for wildcard grants.

A newly introduced concrete permission can immediately match existing wildcard grants.

For example, if:

```text
*
```

is assigned to an Admin, adding:

```text
reports.export
```

does not require adding another permission assignment for that Admin.

The existing wildcard grant already covers it.

---

## 16. User Validity

Authorization shall verify that the referenced user is valid for authorization purposes.

Archived users shall not successfully authorize.

If an authorization check receives an invalid or nonexistent user ID, it shall return `False`.

The authorization layer itself shall not modify the user's authentication session.

Handling a stale session belongs to the authentication/Flask layer.

---

## 17. Archived Users

An archived user shall not receive any permissions through either:

- Direct user permissions.
- Role permissions.

Therefore:

```text
archived user + *
```

still results in denial.

---

## 18. Authorization and Flask

Authorization shall remain independent of Flask.

It shall not directly access:

```python
flask.session
flask.request
```

or other Flask request state.

The Flask layer shall obtain the current authenticated user and pass the user ID to authorization.

The architecture shall therefore be:

```text
Flask
  ↓
current authenticated user
  ↓
has_permission(user_id, permission)
```

---

## 19. Permission Decorators

The Flask-specific `permission_required` decorator belongs to the Flask layer rather than the authorization service.

Its responsibility is to:

1. Obtain the current user from the authentication/session context.
2. Call `has_permission()`.
3. Allow the request when authorization succeeds.
4. Produce the appropriate HTTP behavior when authorization fails.

The authorization service itself shall not perform redirects or return HTTP responses.

---

## 20. Authorization Failures

The authorization layer shall return `False` for an authenticated user who does not have the requested permission.

The Flask layer is responsible for translating this into the appropriate HTTP response.

For example:

```text
authorization:
False

Flask:
403 Forbidden
```

The authorization layer shall not decide whether a denied request should result in:

- `403 Forbidden`.
- A redirect.
- A login page.
- An error page.

---

## 21. Authentication vs Authorization

Authentication and authorization are separate concerns.

Authentication answers:

> Who is this user?

Authorization answers:

> Is this user permitted to perform this operation?

The authorization layer shall assume that the caller has obtained the appropriate user identity.

A missing or stale authentication session is handled by the authentication/Flask layer.

---

## 22. Permission Changes

Authorization checks shall use the current effective permission state.

Permission changes shall therefore take effect on subsequent authorization checks without requiring the affected user to log in again.

For example:

```text
User currently logged in
        ↓
Admin removes inventory.update
        ↓
Next authorization check
        ↓
inventory.update → denied
```

---

## 23. Authorization Side Effects

Permission checks shall be read-only.

Calling:

```python
has_permission(...)
```

shall not modify:

- Users.
- Roles.
- Permissions.
- Sessions.
- Inventory.
- Audit records.

Authorization checks shall have no application-level side effects.

---

## 24. Authorization Data Access

Authorization may directly query the persistent data required to calculate effective permissions.

This includes authorization-specific data such as:

- Users.
- Roles.
- Permissions.
- User-role relationships.
- Role-permission relationships.
- User permission overrides.

Authorization should not directly query unrelated domain data unless the authorization model explicitly requires it.

This avoids unnecessary chains such as:

```text
Authorization
  ↓
generic data service
  ↓
authorization data
```

while keeping authorization from becoming coupled to unrelated domains.

---

## 25. Caching

Authorization results shall not be cached initially.

Each permission check shall evaluate the current effective permission state.

This ensures that permission changes take effect immediately.

Caching may be introduced later if required by measured performance requirements.

---

## 26. Field-Level Permissions

The authorization system shall support permissions that identify individual custom fields through the permission naming convention.

For example:

```text
field.12.read
field.12.update
```

However, the authorization layer shall only determine whether the requested permission is granted.

It shall not itself determine:

- Which fields are displayed in a particular UI.
- How a form is rendered.
- How an asset is serialized for a particular device.
- Which HTTP response is returned.

Those responsibilities belong to the appropriate application/domain layer.

---

## 27. Read Permissions

A permission shall only imply another permission when the authorization rules explicitly define that relationship.

An operation such as:

```text
field.12.update
```

shall not automatically imply:

```text
field.12.read
```

unless an explicit permission rule establishes that behavior.

Wildcard grants remain the mechanism for granting groups of concrete permissions.

For example:

```text
field.*
```

grants all concrete `field.*` permissions without requiring individual assignments.

---

## 28. Authorization Testing

Authorization tests shall verify the effective permission rules independently of Flask.

Tests shall cover, where applicable:

- Exact permission grants.
- Exact permission denial.
- Namespace wildcard grants.
- Global wildcard grants.
- Dynamic wildcard matching.
- Newly introduced permissions matching existing wildcards.
- Permission specificity.
- User-over-role precedence.
- More-specific-over-less-specific precedence.
- Conflicting role permissions.
- Archived users.
- Invalid users.
- Undefined requested permissions.
- Multiple roles.
- Permission changes taking effect immediately.
- No side effects from permission checks.

Flask route/decorator tests shall separately verify that authorization results are translated into the correct HTTP behavior.

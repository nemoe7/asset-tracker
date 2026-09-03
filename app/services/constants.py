"""Shared service-layer constants.

UNSET is the tri-state sentinel used by data-layer update functions:

- An argument left at ``UNSET`` means "leave this field unchanged".
- ``None`` means "explicitly clear the field" (where the field allows NULL).
- Any other value means "set the field to this value".

``UNSET`` is an implementation sentinel: it must never be persisted or
exposed as application data.
"""

UNSET = object()

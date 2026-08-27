from app.services.data.locations import get_location

from .data.audit import create_audit_log
from .data.db import db_transaction
from .data.inventory import get_item, update_item
from .exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemNotFoundError,
)
from .exceptions.data.locations import LocationNotFoundError

_UNSET = object()


def check_item(item_id, location_id=_UNSET):
  with db_transaction():
    item = get_item(
      item_id,
      include_archived=True,
    )

    if item is None:
      raise ItemNotFoundError()

    if item["archived_at"] is not None:
      raise ItemIsArchivedError()

    details = None

    if location_id is not _UNSET:
      location = None

      if location_id is not None:
        location = get_location(location_id)

        if location is None:
          raise LocationNotFoundError()

      update_item(
        item_id,
        location_id=location_id,
      )

      details = {
        "location": location["name"] if location is not None else None,
      }

    create_audit_log(
      action="checked",
      entity_type="inventory_item",
      entity_id=item_id,
      details=details,
    )

  return True

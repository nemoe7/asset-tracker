from .data.audit import create_audit_log
from .data.db import db_transaction
from .data.inventory import get_item
from .exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemNotFoundError,
)


def check_item(item_id):
  with db_transaction():
    item = get_item(
      item_id,
      include_archived=True,
    )

    if item is None:
      raise ItemNotFoundError()

    if item["archived_at"] is not None:
      raise ItemIsArchivedError()

    create_audit_log(
      action="checked",
      entity_type="inventory_item",
      entity_id=item_id,
    )

    return item

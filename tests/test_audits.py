import json

from app.services.audit import (
  create_audit_log,
  get_audit_log,
  get_audit_logs,
)


def test_create_audit_log(test_db):
  audit_id = create_audit_log(
    action="created",
    entity_type="inventory_item",
    entity_id="1",
  )

  audit = get_audit_log(audit_id)

  assert audit["id"] == audit_id
  assert audit["action"] == "created"
  assert audit["entity_type"] == "inventory_item"
  assert audit["entity_id"] == "1"
  assert audit["user_id"] is None
  assert audit["details"] is None
  assert audit["timestamp"] is not None


def test_create_audit_log_with_details(test_db):
  details = {
    "old_location_id": 1,
    "new_location_id": None,
  }

  audit_id = create_audit_log(
    action="location_changed",
    entity_type="inventory_item",
    entity_id="1",
    details=details,
  )

  audit = get_audit_log(audit_id)

  assert json.loads(audit["details"]) == details


def test_get_nonexistent_audit_log(test_db):
  assert get_audit_log(999) is None


def test_get_audit_logs(test_db):
  create_audit_log(
    action="created",
    entity_type="inventory_item",
    entity_id="1",
  )

  create_audit_log(
    action="updated",
    entity_type="inventory_item",
    entity_id="1",
  )

  logs = get_audit_logs()

  assert len(logs) == 2


def test_get_audit_logs_for_entity(test_db):
  create_audit_log(
    action="created",
    entity_type="inventory_item",
    entity_id="1",
  )

  create_audit_log(
    action="updated",
    entity_type="inventory_item",
    entity_id="2",
  )

  create_audit_log(
    action="deleted",
    entity_type="location",
    entity_id="1",
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id="1",
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"
  assert logs[0]["entity_type"] == "inventory_item"
  assert logs[0]["entity_id"] == "1"


def test_get_audit_logs_for_entity_type(test_db):
  create_audit_log(
    action="created",
    entity_type="inventory_item",
    entity_id="1",
  )

  create_audit_log(
    action="created",
    entity_type="location",
    entity_id="1",
  )

  logs = get_audit_logs(
    entity_type="location",
  )

  assert len(logs) == 1
  assert logs[0]["entity_type"] == "location"

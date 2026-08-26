import pytest

from app.services.data.audit import (
  create_audit_log,
  get_audit_log,
  get_audit_logs,
)


def test_create_audit_log(gen_test_data_admin):
  audit_id = create_audit_log(
    action="created",
    entity_type="test",
    entity_id=123,
  )

  assert audit_id is not None

  log = get_audit_log(audit_id)

  assert log is not None
  assert log["id"] == audit_id
  assert log["user_id"] == gen_test_data_admin
  assert log["action"] == "created"
  assert log["entity_type"] == "test"
  assert log["entity_id"] == "123"
  assert log["details"] is None


def test_create_audit_log_with_details(gen_test_data_admin):
  audit_id = create_audit_log(
    action="updated",
    entity_type="test",
    entity_id=123,
    details={
      "name": {
        "old": "Old",
        "new": "New",
      }
    },
  )

  log = get_audit_log(audit_id)

  assert log is not None
  assert log["details"] == {
    "name": {
      "old": "Old",
      "new": "New",
    }
  }


def test_create_audit_log_returns_id(gen_test_data_admin):
  first_id = create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  second_id = create_audit_log(
    action="created",
    entity_type="test",
    entity_id=2,
  )

  assert first_id is not None
  assert second_id is not None
  assert second_id > first_id


def test_get_audit_log_returns_none_for_nonexistent_log(gen_test_data_admin):
  assert get_audit_log(999) is None


def test_get_audit_logs(gen_test_data_admin):
  first_id = create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  second_id = create_audit_log(
    action="updated",
    entity_type="test",
    entity_id=1,
  )

  assert first_id is not None
  assert second_id is not None

  logs = get_audit_logs()

  assert len(logs) == 2
  assert logs[0]["id"] == first_id
  assert logs[1]["id"] == second_id


def test_get_audit_logs_filters_by_entity_type(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=1,
  )

  create_audit_log(
    action="created",
    entity_type="inventory_item",
    entity_id=1,
  )

  logs = get_audit_logs(
    entity_type="user",
  )

  assert len(logs) == 1
  assert logs[0]["entity_type"] == "user"


def test_get_audit_logs_filters_by_entity_id(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=1,
  )

  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=2,
  )

  logs = get_audit_logs(
    entity_id=1,
  )

  assert len(logs) == 1
  assert logs[0]["entity_id"] == "1"


def test_get_audit_logs_filters_by_entity_type_and_id(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=1,
  )

  create_audit_log(
    action="updated",
    entity_type="user",
    entity_id=1,
  )

  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=2,
  )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=1,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"


def test_get_audit_logs_returns_logs_in_id_order(gen_test_data_admin):
  first_id = create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  second_id = create_audit_log(
    action="updated",
    entity_type="test",
    entity_id=1,
  )

  third_id = create_audit_log(
    action="deleted",
    entity_type="test",
    entity_id=1,
  )

  logs = get_audit_logs(
    entity_type="test",
  )

  assert len(logs) == 3
  assert [log["id"] for log in logs] == [
    first_id,
    second_id,
    third_id,
  ]


def test_create_audit_log_without_current_user_fails(
  gen_test_data_db,
):
  with pytest.raises(
    RuntimeError,
    match="No current user",
  ):
    create_audit_log(
      action="created",
      entity_type="test",
      entity_id=1,
    )

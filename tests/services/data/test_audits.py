import pytest

from app.services.data.audit import (
  create_audit_log,
  get_audit_log,
  get_audit_logs,
  list_audit_logs,
)
from app.services.data.db import db_transaction


def _insert_audit_log(
  user_id,
  action,
  entity_type="test",
  entity_id="1",
  timestamp="2026-01-02 12:00:00",
):
  with db_transaction() as connection:
    cursor = connection.execute(
      """
      INSERT INTO audit_log (
        user_id,
        action,
        entity_type,
        entity_id,
        timestamp
      )
      VALUES (?, ?, ?, ?, ?)
      """,
      (
        user_id,
        action,
        entity_type,
        str(entity_id),
        timestamp,
      ),
    )

    return cursor.lastrowid


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


def test_get_audit_logs_tolerates_corrupt_details(gen_test_data_admin):
  with db_transaction() as connection:
    connection.execute(
      """
      INSERT INTO audit_log (
        user_id,
        action,
        entity_type,
        entity_id,
        details,
        timestamp
      )
      VALUES ('1', 'corrupt', 'test', '1', 'not-json', datetime('now'))
      """
    )

  logs = get_audit_logs()

  corrupt = [log for log in logs if log["action"] == "corrupt"]

  assert len(corrupt) == 1
  assert corrupt[0]["details"] == "not-json"


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


def test_list_audit_logs_returns_newest_first(gen_test_data_admin):
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

  result = list_audit_logs()

  assert [log["id"] for log in result["logs"]] == [
    second_id,
    first_id,
  ]


def test_list_audit_logs_includes_username(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  result = list_audit_logs()

  assert result["logs"][0]["username"] == "test_admin"


def test_list_audit_logs_filters_by_action(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  create_audit_log(
    action="updated",
    entity_type="test",
    entity_id=1,
  )

  result = list_audit_logs(action="created")

  assert len(result["logs"]) == 1
  assert result["logs"][0]["action"] == "created"


def test_list_audit_logs_filters_by_user(
  gen_test_data_admin,
  gen_test_data_user,
):
  other_user_id = gen_test_data_user("other_user")

  create_audit_log(
    action="created",
    entity_type="test",
    entity_id=1,
  )

  _insert_audit_log(other_user_id, "updated")

  result = list_audit_logs(user_id=other_user_id)

  assert len(result["logs"]) == 1
  assert result["logs"][0]["user_id"] == other_user_id
  assert result["logs"][0]["action"] == "updated"


def test_list_audit_logs_filters_by_entity_type_and_id(gen_test_data_admin):
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

  result = list_audit_logs(
    entity_type="user",
    entity_id=1,
  )

  assert len(result["logs"]) == 1
  assert result["logs"][0]["entity_id"] == "1"


def test_list_audit_logs_filters_by_date_range(gen_test_data_admin):
  _insert_audit_log(
    gen_test_data_admin,
    "before_range",
    timestamp="2026-01-01 23:59:59",
  )

  _insert_audit_log(
    gen_test_data_admin,
    "in_range_start",
    timestamp="2026-01-02 00:00:00",
  )

  _insert_audit_log(
    gen_test_data_admin,
    "in_range_end",
    timestamp="2026-01-02 23:59:59",
  )

  _insert_audit_log(
    gen_test_data_admin,
    "after_range",
    timestamp="2026-01-03 00:00:00",
  )

  result = list_audit_logs(
    from_date="2026-01-02",
    to_date="2026-01-02",
  )

  assert [log["action"] for log in result["logs"]] == [
    "in_range_end",
    "in_range_start",
  ]
  assert result["total"] == 2


def test_list_audit_logs_paginates_with_total(gen_test_data_admin):
  for _ in range(5):
    create_audit_log(
      action="created",
      entity_type="test",
      entity_id=1,
    )

  first_page = list_audit_logs(limit=2)
  second_page = list_audit_logs(limit=2, offset=2)
  third_page = list_audit_logs(limit=2, offset=4)

  ids = [
    log["id"] for log in first_page["logs"] + second_page["logs"] + third_page["logs"]
  ]

  assert first_page["total"] == 5
  assert len(first_page["logs"]) == 2
  assert len(second_page["logs"]) == 2
  assert len(third_page["logs"]) == 1
  assert len(set(ids)) == 5
  assert ids == sorted(ids, reverse=True)


def test_list_audit_logs_returns_filter_options(gen_test_data_admin):
  create_audit_log(
    action="created",
    entity_type="user",
    entity_id=1,
  )

  create_audit_log(
    action="updated",
    entity_type="inventory_item",
    entity_id=1,
  )

  result = list_audit_logs()

  assert result["entity_types"] == ["inventory_item", "user"]
  assert result["actions"] == ["created", "updated"]

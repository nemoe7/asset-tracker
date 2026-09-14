from app.services.auth.context import reset_current_user, set_current_user
from app.services.data.custom_fields import (
  archive_custom_field,
  create_custom_field,
  get_custom_field,
  get_custom_fields,
)
from app.services.data.permissions import (
  create_permission,
  get_permission_by_name,
)
from app.services.data.role_permissions import set_role_permission
from app.services.data.roles import create_role
from app.services.data.user_roles import set_user_role
from app.services.data.users import create_user


def _login_checker_with_field_grants(
  gen_test_client,
  admin_id,
  read_ids=(),
  update_ids=(),
):
  token = set_current_user(admin_id)

  try:
    user_id = create_user("checker", "checker123", "Checker")
    role_id = create_role("Checker", "Inspects assets")

    for field_id in read_ids:
      name = f"field.{field_id}.read"
      permission = get_permission_by_name(name)
      permission_id = (
        permission["id"] if permission is not None else create_permission(name)
      )
      set_role_permission(role_id, permission_id, True)

    for field_id in update_ids:
      name = f"field.{field_id}.update"
      permission = get_permission_by_name(name)
      permission_id = (
        permission["id"] if permission is not None else create_permission(name)
      )
      set_role_permission(role_id, permission_id, True)

    set_user_role(user_id, role_id)
  finally:
    reset_current_user(token)

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "checker",
      "password": "checker123",
    },
  )


def test_admin_can_create_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  assert response.status_code == 302

  fields = get_custom_fields()
  field = next(field for field in fields if field["name"] == "Serial Number")

  assert field["field_type"] == "text"


def test_admin_can_specify_custom_field_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Purchase Date",
      "field_type": "date",
    },
  )

  assert response.status_code == 302

  fields = get_custom_fields()
  field = next(field for field in fields if field["name"] == "Purchase Date")

  assert field["name"] == "Purchase Date"


def test_admin_can_specify_custom_field_type(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Purchase Date",
      "field_type": "date",
    },
  )

  assert response.status_code == 302

  fields = get_custom_fields()
  field = next(field for field in fields if field["name"] == "Purchase Date")

  assert field["field_type"] == "date"


def test_admin_can_get_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.get(
    f"/custom-fields/{field_id}",
  )

  assert response.status_code == 200
  assert response.json["id"] == field_id
  assert response.json["name"] == "Serial Number"
  assert response.json["field_type"] == "text"


def test_admin_can_update_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}",
    data={
      "name": "Asset Serial Number",
      "field_type": "text",
    },
  )

  assert response.status_code == 302

  field_response = gen_test_admin_client.get(
    f"/custom-fields/{field_id}",
  )

  assert field_response.json["name"] == "Asset Serial Number"


def test_admin_can_archive_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/custom-fields/{field_id}",
  )

  assert response.status_code == 200
  assert response.json["archived_at"] is not None


def test_admin_can_restore_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}/restore",
  )

  assert response.status_code == 302

  field_response = gen_test_admin_client.get(
    f"/custom-fields/{field_id}",
  )

  assert field_response.status_code == 200
  assert field_response.json["archived_at"] is None


def test_admin_cannot_create_custom_field_without_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field name cannot be empty"


def test_admin_cannot_create_custom_field_with_whitespace_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "   ",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field name cannot be empty"


def test_admin_cannot_create_custom_field_with_invalid_type(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Invalid Field",
      "field_type": "invalid",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Invalid custom field type"


def test_admin_cannot_create_duplicate_custom_field(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field already exists"


def test_admin_cannot_update_nonexistent_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields/999999",
    data={
      "name": "Updated Field",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field does not exist"


def test_admin_cannot_archive_nonexistent_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields/999999/archive",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field does not exist"


def test_admin_cannot_restore_active_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Active Field",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}/restore",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field is not archived"


def test_admin_cannot_archive_already_archived_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Archived Field",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field is archived"


def test_admin_can_list_custom_fields(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Purchase Date",
      "field_type": "date",
    },
  )

  response = gen_test_admin_client.get(
    "/custom-fields",
  )

  assert response.status_code == 200

  fields = response.json

  assert len(fields) == 2
  assert fields[0]["name"] == "Purchase Date"
  assert fields[0]["field_type"] == "date"
  assert fields[1]["name"] == "Serial Number"
  assert fields[1]["field_type"] == "text"


def test_custom_field_list_respects_read_permission(
  gen_test_admin,
  gen_test_client,
):
  token = set_current_user(gen_test_admin)

  try:
    visible_id = create_custom_field("Serial", "text")
    create_custom_field("Secret", "text")
  finally:
    reset_current_user(token)

  _login_checker_with_field_grants(
    gen_test_client,
    gen_test_admin,
    read_ids={visible_id},
  )

  response = gen_test_client.get("/custom-fields")

  assert response.status_code == 200

  fields = response.json

  assert [field["name"] for field in fields] == ["Serial"]
  assert fields[0]["is_editable"] is False


def test_custom_field_list_marks_editable(
  gen_test_admin,
  gen_test_client,
):
  token = set_current_user(gen_test_admin)

  try:
    field_id = create_custom_field("Serial", "text")
  finally:
    reset_current_user(token)

  _login_checker_with_field_grants(
    gen_test_client,
    gen_test_admin,
    read_ids={field_id},
    update_ids={field_id},
  )

  response = gen_test_client.get("/custom-fields")

  assert response.status_code == 200

  assert response.json[0]["is_editable"] is True


def test_custom_field_get_requires_read_permission(
  gen_test_admin,
  gen_test_client,
):
  token = set_current_user(gen_test_admin)

  try:
    field_id = create_custom_field("Secret", "text")
  finally:
    reset_current_user(token)

  _login_checker_with_field_grants(
    gen_test_client,
    gen_test_admin,
  )

  response = gen_test_client.get(f"/custom-fields/{field_id}")

  assert response.status_code == 404


def test_admin_can_list_archived_custom_fields(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  response = gen_test_admin_client.get(
    "/custom-fields?include_archived=true",
  )

  assert response.status_code == 200

  fields = response.json

  assert len(fields) == 1
  assert fields[0]["id"] == field_id
  assert fields[0]["archived_at"] is not None


def test_admin_list_excludes_archived_custom_fields(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  response = gen_test_admin_client.get(
    "/custom-fields",
  )

  assert response.status_code == 200
  assert response.json == []


def test_admin_cannot_get_nonexistent_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/custom-fields/999999",
  )

  assert response.status_code == 404
  assert response.json["error"] == "Custom field not found"


def test_admin_cannot_update_custom_field_with_empty_name(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}",
    data={
      "name": "",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field name cannot be empty"


def test_admin_cannot_update_custom_field_with_invalid_type(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}",
    data={
      "field_type": "invalid",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Invalid custom field type"


def test_admin_cannot_update_custom_field_to_duplicate_name(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  second_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Asset Tag",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  second_id = second_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{second_id}",
    data={
      "name": "Serial Number",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field already exists"


def test_admin_cannot_update_archived_custom_field(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  gen_test_admin_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}",
    data={
      "name": "Asset Tag",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "Custom field is archived"


def test_admin_cannot_update_custom_field_without_fields(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{field_id}",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"] == "No fields to update"


def test_custom_field_create_requires_field_create_permission(
  gen_test_client,
  gen_test_admin,
  gen_user_with_permission,
):
  gen_user_with_permission("field.create")

  create_response = gen_test_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert create_response.status_code == 200
  field_id = create_response.json["id"]

  archive_response = gen_test_client.post(
    f"/custom-fields/{field_id}/archive",
  )

  assert archive_response.status_code == 403


def test_custom_field_update_requires_field_update_permission(
  gen_test_client,
  gen_test_admin,
  gen_user_with_permission,
):
  token = set_current_user(gen_test_admin)

  try:
    field_id = create_custom_field("Serial", "text")
  finally:
    reset_current_user(token)

  gen_user_with_permission(f"field.{field_id}.update")

  response = gen_test_client.post(
    f"/custom-fields/{field_id}",
    data={
      "name": "Asset Serial",
    },
  )

  assert response.status_code == 302

  token = set_current_user(gen_test_admin)

  try:
    renamed = get_custom_field(field_id)
  finally:
    reset_current_user(token)

  assert renamed["name"] == "Asset Serial"

  create_response = gen_test_client.post(
    "/custom-fields",
    data={
      "name": "Other",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert create_response.status_code == 403


def test_custom_field_restore_uses_field_create_permission(
  gen_test_client,
  gen_test_admin,
  gen_user_with_permission,
):
  token = set_current_user(gen_test_admin)

  try:
    field_id = create_custom_field("Serial", "text")
    archive_custom_field(field_id)
  finally:
    reset_current_user(token)

  gen_user_with_permission("field.create")

  response = gen_test_client.post(
    f"/custom-fields/{field_id}/restore",
  )

  assert response.status_code == 302

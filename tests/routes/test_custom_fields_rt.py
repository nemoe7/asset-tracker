from app.services.data.custom_fields import get_custom_fields


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
  )

  assert response.status_code == 400
  assert b"Custom field name cannot be empty" in response.data


def test_admin_cannot_create_custom_field_with_whitespace_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "   ",
      "field_type": "text",
    },
  )

  assert response.status_code == 400
  assert b"Custom field name cannot be empty" in response.data


def test_admin_cannot_create_custom_field_with_invalid_type(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Invalid Field",
      "field_type": "invalid",
    },
  )

  assert response.status_code == 400
  assert b"Invalid custom field type" in response.data


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
  )

  assert response.status_code == 400
  assert b"Custom field already exists" in response.data


def test_admin_cannot_update_nonexistent_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields/999999",
    data={
      "name": "Updated Field",
    },
  )

  assert response.status_code == 400
  assert b"Custom field does not exist" in response.data


def test_admin_cannot_archive_nonexistent_custom_field(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/custom-fields/999999/archive",
  )

  assert response.status_code == 400
  assert b"Custom field does not exist" in response.data


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
  )

  assert response.status_code == 400
  assert b"Custom field is not archived" in response.data


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
  )

  assert response.status_code == 400
  assert b"Custom field is archived" in response.data


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
  assert b"Custom field not found" in response.data


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
  )

  assert response.status_code == 400
  assert b"Custom field name cannot be empty" in response.data


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
  )

  assert response.status_code == 400
  assert b"Invalid custom field type" in response.data


def test_admin_cannot_update_custom_field_to_duplicate_name(
  gen_test_admin_client,
):
  first_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
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

  first_id = first_response.json["id"]
  second_id = second_response.json["id"]

  response = gen_test_admin_client.post(
    f"/custom-fields/{second_id}",
    data={
      "name": "Serial Number",
    },
  )

  assert response.status_code == 400
  assert b"Custom field already exists" in response.data


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
  )

  assert response.status_code == 400
  assert b"Custom field is archived" in response.data


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
  )

  assert response.status_code == 400
  assert b"No fields to update" in response.data

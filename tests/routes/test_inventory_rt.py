def test_admin_can_create_asset(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


def test_admin_cannot_create_asset_without_name(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_view_created_asset(gen_test_admin_client):
  create_response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
  )

  assert create_response.status_code == 302

  response = gen_test_admin_client.get("/")

  assert response.status_code == 200
  assert b"Test Asset" in response.data


def test_admin_can_edit_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "name": "Updated Asset",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.status_code == 200
  assert response.json["name"] == "Updated Asset"


def test_admin_can_archive_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.status_code == 404


def test_archived_asset_can_be_viewed(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}?include_archived=true",
  )

  assert response.status_code == 200
  print(response.json)
  assert response.json["id"] == item_id
  assert response.json["archived_at"] is not None


def test_admin_can_restore_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/restore",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}?include_archived=true",
  )

  assert response.status_code == 200
  assert response.json["id"] == item_id
  assert response.json["archived_at"] is None


def test_admin_can_update_asset_custom_field_value(
  gen_test_admin_client,
  gen_test_item,
):
  field_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_name = field_response.json["name"]
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      f"f_{field_name}": "SN12345",
      "name": "Test Asset",
    },
  )

  assert response.status_code == 302

  item_response = gen_test_admin_client.get(
    f"/inventory/{item_id}",
  )

  assert item_response.status_code == 200
  assert item_response.json["custom_fields"][field_name] == "SN12345"


def test_admin_cannot_update_asset_with_invalid_location(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item()

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "location_id": "999999",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_update_nonexistent_asset(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/inventory/does-not-exist",
    data={
      "name": "Updated Asset",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_check_item(gen_test_admin_client, gen_test_item):
  item_id = gen_test_item("Laptop")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/check",
  )

  assert response.status_code == 200
  assert response.json["id"] == item_id
  assert response.json["name"] == "Laptop"
  assert response.json["location_id"] is None


def test_check_item_not_found(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/does-not-exist/check",
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_check_item_archived(gen_test_admin_client, gen_test_item):
  item_id = gen_test_item("Laptop")

  gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/check",
  )

  assert response.status_code == 400
  assert response.json["error"]

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

  assert response.status_code == 302
  assert response.location.endswith("/")


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

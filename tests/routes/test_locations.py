from app.services.data.locations import get_location


def test_admin_can_create_location(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
  )

  assert response.status_code == 302


def test_admin_can_create_location_with_description(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
      "description": "Main storage area",
    },
  )

  assert response.status_code == 302


def test_admin_cannot_create_location_without_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_create_location_with_whitespace_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "   ",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_create_duplicate_location(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
  )

  response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_list_locations(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
      "description": "Main storage area",
    },
  )

  gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Office",
      "description": "Main office",
    },
  )

  response = gen_test_admin_client.get(
    "/locations",
  )

  assert response.status_code == 200


def test_admin_can_get_location(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
      "description": "Main storage area",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.get(
    f"/locations/{location_id}",
  )

  assert response.status_code == 200
  assert response.json["id"] == location_id
  assert response.json["name"] == "Warehouse"
  assert response.json["description"] == "Main storage area"


def test_admin_cannot_get_nonexistent_location(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/locations/999999",
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_admin_can_update_location_name(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    data={
      "name": "Main Warehouse",
    },
  )

  assert response.status_code == 302

  location = get_location(location_id)

  assert location["name"] == "Main Warehouse"


def test_admin_can_update_location_description(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
      "description": "Old description",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    data={
      "description": "New description",
    },
  )

  assert response.status_code == 302

  location = get_location(location_id)

  assert location["description"] == "New description"


def test_admin_can_update_location_name_and_description(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
      "description": "Old description",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    data={
      "name": "Main Warehouse",
      "description": "New description",
    },
  )

  assert response.status_code == 302

  location = get_location(location_id)

  assert location["name"] == "Main Warehouse"
  assert location["description"] == "New description"


def test_admin_cannot_update_location_with_empty_name(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    data={
      "name": "",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_update_location_to_duplicate_name(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
  )

  second_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Office",
    },
    headers={
      "Accept": "application/json",
    },
  )

  second_id = second_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{second_id}",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_update_nonexistent_location(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations/999999",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_admin_cannot_update_location_without_fields(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_delete_location(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}/delete",
    data={
      "confirm": "true",
    },
  )

  assert response.status_code == 302
  assert get_location(location_id) is None


def test_admin_cannot_delete_nonexistent_location(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/locations/999999/delete",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_admin_can_update_location_with_json_response(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}",
    data={
      "name": "Main Warehouse",
      "description": "Updated description",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200
  assert response.json["id"] == location_id
  assert response.json["name"] == "Main Warehouse"
  assert response.json["description"] == "Updated description"


def test_admin_can_delete_location_with_json_response(
  gen_test_admin_client,
):
  create_response = gen_test_admin_client.post(
    "/locations",
    data={
      "name": "Warehouse",
    },
    headers={
      "Accept": "application/json",
    },
  )

  location_id = create_response.json["id"]

  response = gen_test_admin_client.post(
    f"/locations/{location_id}/delete",
    data={
      "confirm": "true",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200
  assert response.json["deleted"] is True
  assert response.json["id"] == location_id
  assert get_location(location_id) is None

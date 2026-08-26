def test_admin_can_create_asset(
  test_admin_client,
):
  response = test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


def test_admin_cannot_create_asset_without_name(test_admin_client):
  response = test_admin_client.post(
    "/inventory",
    data={
      "name": "",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


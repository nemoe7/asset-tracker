def test_admin_can_view_inventory_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get("/")

  assert response.status_code == 200


def test_inventory_page_displays_asset(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Test Asset")

  response = gen_test_admin_client.get("/")

  assert response.status_code == 200
  assert b"Test Asset" in response.data


def test_unauthenticated_user_is_redirected_to_login(
  gen_test_client,
):
  response = gen_test_client.get("/")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")

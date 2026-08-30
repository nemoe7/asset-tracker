import pytest


@pytest.fixture(autouse=True)
def setup_admin(page, live_server, gen_password):
  password = gen_password("test_admin")

  response = page.request.post(
    f"{live_server}/auth/setup",
    form={
      "username": "test_admin",
      "display_name": "Test Admin",
      "password": password,
      "confirm_password": password,
    },
    max_redirects=0,
  )

  assert response.status == 302

  return {
    "username": "test_admin",
    "password": password,
  }


@pytest.fixture
def create_item(page, live_server):
  def _create(name, location_id=None):
    response = page.request.post(
      f"{live_server}/inventory",
      form={
        "name": name,
        "location_id": location_id or "",
      },
      max_redirects=0,
    )

    assert response.status == 302

  return _create

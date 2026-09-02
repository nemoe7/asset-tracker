import pytest


@pytest.fixture
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
def create_location(page, live_server):
  def _create(name):
    response = page.request.post(
      f"{live_server}/locations",
      form={
        "name": name,
      },
      headers={
        "Accept": "application/json",
      },
      max_redirects=0,
    )

    assert response.status == 200
    assert response.json()["id"]

    return response.json()

  return _create
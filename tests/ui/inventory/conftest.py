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
      headers={
        "Accept": "application/json",
      },
      max_redirects=0,
    )

    assert response.status == 200
    assert response.json()["id"]

    return response.json()

  return _create


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


@pytest.fixture
def create_custom_field(page, live_server):
  def _create(name, field_type, required=False, enum_values=None, description=None):
    data = {
      "name": name,
      # Enum fields cannot be created without values; create as text and
      # switch the type together with the values below.
      "field_type": "text" if field_type == "enum" else field_type,
    }

    response = page.request.post(
      f"{live_server}/custom-fields",
      form=data,
      max_redirects=0,
    )

    assert response.status == 302

    fields = page.request.get(f"{live_server}/custom-fields").json()
    field = next(candidate for candidate in fields if candidate["name"] == name)

    if required or description is not None:
      update = {}

      if required:
        update["required"] = "true"

      if description is not None:
        update["description"] = description

      page.request.post(
        f"{live_server}/custom-fields/{field['id']}",
        form=update,
        max_redirects=0,
      )

      fields = page.request.get(f"{live_server}/custom-fields").json()
      field = next(candidate for candidate in fields if candidate["id"] == field["id"])

    if field_type == "enum":
      # Enum fields cannot be created directly without values; create as
      # text, then switch the type together with the values.
      page.request.post(
        f"{live_server}/custom-fields/{field['id']}",
        form={
          "field_type": "enum",
          "enum_values": ",".join(enum_values),
        },
        max_redirects=0,
      )

      fields = page.request.get(f"{live_server}/custom-fields").json()
      field = next(candidate for candidate in fields if candidate["id"] == field["id"])

    return field

  return _create


@pytest.fixture
def set_item_custom_field(page, live_server):
  def _set(item_id, name, value):
    response = page.request.post(
      f"{live_server}/inventory/{item_id}",
      form={
        f"f_{name}": value,
      },
      max_redirects=0,
    )

    assert response.status == 302

  return _set

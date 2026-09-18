import pytest

from app.services.auth.context import reset_current_user, set_current_user
from app.services.data.export_templates import create_export_template
from app.services.data.users import create_user


@pytest.fixture
def admin_id(gen_test_admin):
  from app.services.data.users import get_user_by_username

  return get_user_by_username("test_admin")["id"]


@pytest.fixture
def admin_template_id(admin_id):
  token = set_current_user(admin_id)

  try:
    return create_export_template(
      admin_id,
      "Admin template",
      {"columns": ["name", "location"]},
    )
  finally:
    reset_current_user(token)


@pytest.fixture
def other_user_id(admin_id, gen_password):
  token = set_current_user(admin_id)

  try:
    return create_user("bob", gen_password("bob"), "Bob")
  finally:
    reset_current_user(token)


@pytest.fixture
def other_template_id(other_user_id):
  token = set_current_user(other_user_id)

  try:
    return create_export_template(
      other_user_id,
      "Bob template",
      {"columns": ["name"]},
    )
  finally:
    reset_current_user(token)


def test_list_templates_requires_login(gen_test_client):
  response = gen_test_client.get("/export-templates")

  assert response.status_code == 302


def test_list_templates_returns_json(
  gen_test_admin_client,
  admin_template_id,
  other_template_id,
):
  response = gen_test_admin_client.get("/export-templates")

  assert response.status_code == 200

  templates = response.json
  names = {t["name"] for t in templates}

  # Users see their own personal templates plus shared ones only.
  assert names == {"Admin template"}
  assert all("configuration" in t and "shared" in t for t in templates)


def test_create_template_requires_login(gen_test_client):
  response = gen_test_client.post(
    "/export-templates",
    json={"name": "T", "configuration": {}},
  )

  assert response.status_code == 302


def test_create_personal_template(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/export-templates",
    json={
      "name": "Mine",
      "configuration": {"columns": ["name"]},
    },
  )

  assert response.status_code == 201
  assert response.json["shared"] is False

  listing = gen_test_admin_client.get("/export-templates").json
  assert any(t["name"] == "Mine" for t in listing)


def test_create_shared_template_as_admin(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/export-templates",
    json={
      "name": "Shared",
      "configuration": {"columns": ["name"]},
      "shared": True,
    },
  )

  assert response.status_code == 201
  assert response.json["shared"] is True


def test_create_shared_template_as_non_admin_forbidden(
  gen_test_client,
  other_user_id,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.post(
    "/export-templates",
    json={
      "name": "Shared",
      "configuration": {},
      "shared": True,
    },
  )

  assert response.status_code == 403


def test_create_template_invalid_input(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/export-templates",
    json={"name": "", "configuration": {"unknown": 1}},
  )

  assert response.status_code == 400
  assert response.json["error"]

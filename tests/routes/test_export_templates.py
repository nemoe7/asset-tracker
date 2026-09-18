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


def test_apply_template_redirects_with_params(
  gen_test_admin_client,
  admin_template_id,
):
  response = gen_test_admin_client.post(
    f"/export-templates/{admin_template_id}/apply",
  )

  assert response.status_code == 302

  location = response.headers["Location"]
  assert "/inventory/export" in location
  assert "fields=name" in location
  assert "fields=location" in location


def test_apply_template_hidden_template_is_404(
  gen_test_client,
  other_user_id,
  other_template_id,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  # Bob's own personal template: applying works.
  response = gen_test_client.post(f"/export-templates/{other_template_id}/apply")

  assert response.status_code == 302


def test_apply_missing_template_is_404(gen_test_admin_client):
  response = gen_test_admin_client.post("/export-templates/9999/apply")

  assert response.status_code == 404


def test_update_own_template(
  gen_test_client,
  other_user_id,
  other_template_id,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.put(
    f"/export-templates/{other_template_id}",
    json={"name": "Renamed"},
  )

  assert response.status_code == 200
  assert response.json["name"] == "Renamed"


def test_update_shared_template_by_non_admin_forbidden(
  gen_test_admin_client,
  admin_template_id,
  gen_test_client,
  other_user_id,
  gen_password,
):
  # Make the admin template shared via data layer.
  from app.services.data.db import db_transaction

  with db_transaction() as connection:
    connection.execute(
      """
      UPDATE export_templates SET user_id = NULL WHERE id = ?
      """,
      (admin_template_id,),
    )

  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.put(
    f"/export-templates/{admin_template_id}",
    json={"name": "Hacked"},
  )

  assert response.status_code == 403


def test_update_other_users_personal_template_is_404(
  gen_test_client,
  other_user_id,
  admin_template_id,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.put(
    f"/export-templates/{admin_template_id}",
    json={"name": "Hacked"},
  )

  assert response.status_code == 404


def test_delete_own_template(
  gen_test_client,
  other_user_id,
  other_template_id,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.delete(f"/export-templates/{other_template_id}")

  assert response.status_code in (200, 204)

  listing = gen_test_client.get("/export-templates").json
  assert not any(t["id"] == other_template_id for t in listing)


def test_delete_shared_template_by_non_admin_forbidden(
  gen_test_client,
  other_user_id,
  gen_password,
  admin_template_id,
):
  from app.services.data.db import db_transaction

  with db_transaction() as connection:
    connection.execute(
      """
      UPDATE export_templates SET user_id = NULL WHERE id = ?
      """,
      (admin_template_id,),
    )

  gen_test_client.post(
    "/auth/login",
    data={"username": "bob", "password": gen_password("bob")},
  )

  response = gen_test_client.delete(f"/export-templates/{admin_template_id}")

  assert response.status_code == 403


def test_delete_requires_login(gen_test_client):
  response = gen_test_client.delete("/export-templates/1")

  assert response.status_code == 302


def test_apply_template_unreadable_field_exports_only_readable(
  gen_test_admin,
  gen_test_admin_client,
  admin_template_id,
):
  # EXP-008: even if a saved template lists columns the user cannot
  # read, build_export's visible_field_ids filtering limits the output.
  from app.services.data.db import db_transaction

  with db_transaction() as connection:
    connection.execute(
      """
      UPDATE export_templates
      SET configuration = ?
      WHERE id = ?
      """,
      ('{"columns": ["name", "not_a_field"]}', admin_template_id),
    )

  response = gen_test_admin_client.post(
    f"/export-templates/{admin_template_id}/apply",
  )

  # The redirect target enforces column validity: unknown column in the
  # saved template fails validation at the export endpoint.
  assert response.status_code == 302

  follow = gen_test_admin_client.get(
    "/inventory/export",
    query_string=response.location.split("?", 1)[-1],
  )

  assert follow.status_code == 400
  assert follow.json["error"]

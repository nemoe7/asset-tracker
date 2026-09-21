def test_admin_can_list_users(gen_test_admin_client):
  response = gen_test_admin_client.get(
    "/users",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200

  users = response.json
  assert isinstance(users, list)

  admin = next(user for user in users if user["username"] == "test_admin")
  assert admin["name"] == "Test Admin"
  assert set(admin.keys()) == {"id", "username", "name"}


def test_users_list_is_ordered_by_username(gen_test_admin_client, gen_test_admin):
  response = gen_test_admin_client.get(
    "/users",
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200

  usernames = [user["username"] for user in response.json]
  assert usernames == sorted(usernames)


def test_users_list_excludes_archived_users(gen_test_admin_client, gen_test_admin):
  create_response = gen_test_admin_client.post(
    "/admin/users",
    data={
      "username": "doomed_user",
      "password": "doomed_password",
    },
  )

  assert create_response.status_code == 302

  from app.services.data.users import get_user_by_username

  user_id = get_user_by_username("doomed_user")["id"]

  archive_response = gen_test_admin_client.post(f"/admin/users/{user_id}/archive")
  assert archive_response.status_code == 302

  response = gen_test_admin_client.get("/users")

  assert response.status_code == 200
  assert all(user["username"] != "doomed_user" for user in response.json)


def test_users_list_requires_users_read_permission(
  gen_test_client,
  gen_test_admin,
  gen_user_with_permission,
):
  gen_user_with_permission("inventory.read")

  response = gen_test_client.get("/users")

  assert response.status_code == 403


def test_users_list_allows_users_read_permission(
  gen_test_client,
  gen_test_admin,
  gen_user_with_permission,
):
  gen_user_with_permission("users.read")

  response = gen_test_client.get("/users")

  assert response.status_code == 200
  assert isinstance(response.json, list)


def test_users_list_requires_login(gen_test_client):
  response = gen_test_client.get("/users")

  assert response.status_code == 302

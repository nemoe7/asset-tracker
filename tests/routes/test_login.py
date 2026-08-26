def test_admin_can_login(test_admin, test_client, gen_test_password):
  response = test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_test_password("test_admin"),
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


def test_admin_login_sets_session(
  test_admin,
  test_client,
  gen_test_password,
):
  test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_test_password("test_admin"),
    },
  )

  with test_client.session_transaction() as session:
    assert session["user_id"] == test_admin
    assert session.permanent is True


def test_admin_login_rejects_invalid_password(
  test_admin,
  test_client,
  gen_test_password,
):
  response = test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": "wrong_password",
    },
  )

  assert response.status_code == 200
  assert b"Invalid username or password." in response.data


def test_unauthenticated_user_is_redirected_to_login(
  test_client,
):
  response = test_client.get("/")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")

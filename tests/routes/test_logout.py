def test_admin_can_logout(
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

  response = test_client.post("/auth/logout")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")


def test_admin_logout_clears_session(
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

  test_client.post("/auth/logout")

  with test_client.session_transaction() as session:
    assert "user_id" not in session

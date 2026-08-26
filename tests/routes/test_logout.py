def test_admin_can_logout(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  response = gen_test_client.post("/auth/logout")

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")


def test_admin_logout_clears_session(
  gen_test_admin,
  gen_test_client,
  gen_password,
):
  gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
  )

  gen_test_client.post("/auth/logout")

  with gen_test_client.session_transaction() as session:
    assert "user_id" not in session

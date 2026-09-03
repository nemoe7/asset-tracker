def test_cross_site_post_is_rejected(gen_test_client):
  response = gen_test_client.post(
    "/auth/login",
    data={"username": "admin", "password": "password"},
    headers={"Sec-Fetch-Site": "cross-site"},
  )

  assert response.status_code == 403


def test_same_origin_post_is_allowed(gen_test_admin, gen_test_client, gen_password):
  response = gen_test_client.post(
    "/auth/login",
    data={
      "username": "test_admin",
      "password": gen_password("test_admin"),
    },
    headers={"Sec-Fetch-Site": "same-origin"},
  )

  assert response.status_code == 302


def test_post_without_sec_fetch_site_header_is_allowed(gen_test_client):
  response = gen_test_client.post(
    "/auth/login",
    data={"username": "admin", "password": "password"},
  )

  assert response.status_code != 403


def test_cross_site_get_is_allowed(gen_test_client):
  response = gen_test_client.get(
    "/auth/login",
    headers={"Sec-Fetch-Site": "cross-site"},
  )

  assert response.status_code != 403

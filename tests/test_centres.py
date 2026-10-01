class TestCentres:
    def test_list_centres(self, client, user_headers, sample_centre):
        resp = client.get("/centres/", headers=user_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1
        assert data[0]["name"] == "Test Centre"

    def test_get_centre(self, client, user_headers, sample_centre):
        resp = client.get(f"/centres/{sample_centre.id}", headers=user_headers)
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Test Centre"

    def test_get_nonexistent_centre(self, client, user_headers):
        resp = client.get("/centres/9999", headers=user_headers)
        assert resp.status_code == 404

    def test_admin_create_centre(self, client, admin_headers):
        resp = client.post("/centres/", headers=admin_headers, json={
            "name": "New Centre",
            "location": "New City",
        })
        assert resp.status_code == 201
        assert resp.get_json()["name"] == "New Centre"

    def test_normal_user_cannot_create_centre(self, client, user_headers):
        resp = client.post("/centres/", headers=user_headers, json={
            "name": "Forbidden",
            "location": "Nowhere",
        })
        assert resp.status_code == 403

    def test_admin_update_centre(self, client, admin_headers, sample_centre):
        resp = client.patch(
            f"/centres/{sample_centre.id}",
            headers=admin_headers,
            json={"name": "Updated Centre"},
        )
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Updated Centre"

    def test_get_centre_tests(self, client, user_headers, sample_centre_test):
        centre_id = sample_centre_test.centre_id
        resp = client.get(f"/centres/{centre_id}/tests", headers=user_headers)
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) == 1
        assert data[0]["price"] == 500.0


class TestTests:
    def test_list_tests(self, client, user_headers, sample_test):
        resp = client.get("/tests/", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()) >= 1

    def test_get_test(self, client, user_headers, sample_test):
        resp = client.get(f"/tests/{sample_test.id}", headers=user_headers)
        assert resp.status_code == 200
        assert resp.get_json()["name"] == "Blood Test"

    def test_get_nonexistent_test(self, client, user_headers):
        resp = client.get("/tests/9999", headers=user_headers)
        assert resp.status_code == 404

    def test_admin_create_test(self, client, admin_headers):
        resp = client.post("/tests/", headers=admin_headers, json={
            "name": "X-Ray",
            "description": "Chest X-Ray",
        })
        assert resp.status_code == 201

    def test_normal_user_cannot_create_test(self, client, user_headers):
        resp = client.post("/tests/", headers=user_headers, json={
            "name": "Forbidden Test",
        })
        assert resp.status_code == 403

    def test_create_centre_test(self, client, admin_headers, sample_centre, sample_test):
        resp = client.post("/tests/centre-tests", headers=admin_headers, json={
            "centre_id": sample_centre.id,
            "test_id": sample_test.id,
            "price": 750,
        })
        assert resp.status_code == 201
        assert resp.get_json()["price"] == 750.0

    def test_duplicate_centre_test(self, client, admin_headers, sample_centre_test):
        resp = client.post("/tests/centre-tests", headers=admin_headers, json={
            "centre_id": sample_centre_test.centre_id,
            "test_id": sample_centre_test.test_id,
            "price": 999,
        })
        assert resp.status_code == 409

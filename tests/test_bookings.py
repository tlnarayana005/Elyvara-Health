from datetime import datetime, timedelta, timezone


def future_dt():
    """Return an ISO 8601 datetime string 7 days in the future."""
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


class TestBookingCreation:
    def test_create_booking_success(self, client, user_headers, sample_centre_test):
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "PENDING"
        # Server-side pricing: must match DB price, not any client value
        assert data["amount"] == 500.0

    def test_server_side_price_ignores_client_amount(self, client, user_headers, sample_centre_test):
        """Even if the client sends an 'amount' field, the server must use DB price."""
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
            "amount": 1,  # malicious attempt
        })
        assert resp.status_code == 201
        assert resp.get_json()["amount"] == 500.0  # DB price wins

    def test_invalid_centre_test(self, client, user_headers):
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": 9999,
            "appointment_datetime": future_dt(),
        })
        assert resp.status_code == 404

    def test_past_appointment(self, client, user_headers, sample_centre_test):
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": past,
        })
        assert resp.status_code == 400

    def test_missing_fields(self, client, user_headers):
        resp = client.post("/bookings/", headers=user_headers, json={})
        assert resp.status_code == 400


class TestBookingRetrieval:
    def test_list_own_bookings(self, client, user_headers, sample_centre_test):
        # Create a booking
        client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        resp = client.get("/bookings/", headers=user_headers)
        assert resp.status_code == 200
        assert len(resp.get_json()) == 1

    def test_get_own_booking(self, client, user_headers, sample_centre_test):
        create_resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = create_resp.get_json()["id"]
        resp = client.get(f"/bookings/{booking_id}", headers=user_headers)
        assert resp.status_code == 200

    def test_cannot_access_other_users_booking(
        self, client, user_headers, other_user_headers, sample_centre_test
    ):
        # user creates booking
        create_resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = create_resp.get_json()["id"]
        # other_user tries to access it
        resp = client.get(f"/bookings/{booking_id}", headers=other_user_headers)
        assert resp.status_code == 403

    def test_nonexistent_booking(self, client, user_headers):
        resp = client.get("/bookings/9999", headers=user_headers)
        assert resp.status_code == 404


class TestBookingCancellation:
    def test_cancel_pending_booking(self, client, user_headers, sample_centre_test):
        create_resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = create_resp.get_json()["id"]
        resp = client.post(f"/bookings/{booking_id}/cancel", headers=user_headers)
        assert resp.status_code == 200
        assert resp.get_json()["status"] == "CANCELLED"

    def test_cannot_cancel_already_cancelled(self, client, user_headers, sample_centre_test):
        create_resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = create_resp.get_json()["id"]
        client.post(f"/bookings/{booking_id}/cancel", headers=user_headers)
        # Try cancelling again
        resp = client.post(f"/bookings/{booking_id}/cancel", headers=user_headers)
        assert resp.status_code == 409

    def test_other_user_cannot_cancel(
        self, client, user_headers, other_user_headers, sample_centre_test
    ):
        create_resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = create_resp.get_json()["id"]
        resp = client.post(f"/bookings/{booking_id}/cancel", headers=other_user_headers)
        assert resp.status_code == 403

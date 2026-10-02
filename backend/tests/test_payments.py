from datetime import datetime, timedelta, timezone


def future_dt():
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


class TestPaymentCreation:
    def _create_booking(self, client, user_headers, sample_centre_test):
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        return resp.get_json()["id"]

    def test_successful_payment(self, client, user_headers, sample_centre_test):
        booking_id = self._create_booking(client, user_headers, sample_centre_test)
        resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["status"] == "SUCCESS"
        assert data["amount"] == 500.0

        # Verify booking is now CONFIRMED
        booking_resp = client.get(f"/bookings/{booking_id}", headers=user_headers)
        assert booking_resp.get_json()["status"] == "CONFIRMED"

    def test_failed_payment(self, client, user_headers, sample_centre_test):
        booking_id = self._create_booking(client, user_headers, sample_centre_test)
        resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
            "simulate_failure": True,
        })
        assert resp.status_code == 201
        assert resp.get_json()["status"] == "FAILED"

        # Verify booking is now FAILED
        booking_resp = client.get(f"/bookings/{booking_id}", headers=user_headers)
        assert booking_resp.get_json()["status"] == "FAILED"

    def test_payment_nonexistent_booking(self, client, user_headers):
        resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": 9999,
        })
        assert resp.status_code == 404

    def test_payment_other_users_booking(
        self, client, user_headers, other_user_headers, sample_centre_test
    ):
        booking_id = self._create_booking(client, user_headers, sample_centre_test)
        resp = client.post("/payments/", headers=other_user_headers, json={
            "booking_id": booking_id,
        })
        assert resp.status_code == 403

    def test_cannot_pay_already_confirmed(self, client, user_headers, sample_centre_test):
        booking_id = self._create_booking(client, user_headers, sample_centre_test)
        # First payment succeeds
        client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
        })
        # Second payment attempt
        resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
        })
        assert resp.status_code == 409

    def test_cannot_pay_cancelled_booking(self, client, user_headers, sample_centre_test):
        booking_id = self._create_booking(client, user_headers, sample_centre_test)
        client.post(f"/bookings/{booking_id}/cancel", headers=user_headers)
        resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
        })
        assert resp.status_code == 409

from datetime import datetime, timedelta, timezone

from app.models.webhook_event import WebhookEvent
from app.models.payment import Payment
from app.models.booking import Booking


def future_dt():
    return (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()


def _setup_booking_and_payment(client, user_headers, sample_centre_test, db):
    """Helper: create a booking + payment, return (booking_id, provider_payment_id)."""
    resp = client.post("/bookings/", headers=user_headers, json={
        "centre_test_id": sample_centre_test.id,
        "appointment_datetime": future_dt(),
    })
    booking_id = resp.get_json()["id"]

    pay_resp = client.post("/payments/", headers=user_headers, json={
        "booking_id": booking_id,
    })
    provider_payment_id = pay_resp.get_json()["provider_payment_id"]
    return booking_id, provider_payment_id


class TestWebhookSuccess:
    def test_webhook_success(self, client, user_headers, sample_centre_test, db):
        booking_id, pay_id = _setup_booking_and_payment(
            client, user_headers, sample_centre_test, db
        )
        resp = client.post("/payments/webhook/", json={
            "event_id": "evt_001",
            "event_type": "payment.updated",
            "payment_id": pay_id,
            "status": "SUCCESS",
        })
        assert resp.status_code == 200
        assert resp.get_json()["payment_status"] == "SUCCESS"

    def test_webhook_failed_status(self, client, user_headers, sample_centre_test, db):
        # Create booking + payment that simulates failure to keep PENDING state
        resp = client.post("/bookings/", headers=user_headers, json={
            "centre_test_id": sample_centre_test.id,
            "appointment_datetime": future_dt(),
        })
        booking_id = resp.get_json()["id"]

        pay_resp = client.post("/payments/", headers=user_headers, json={
            "booking_id": booking_id,
            "simulate_failure": True,
        })
        pay_id = pay_resp.get_json()["provider_payment_id"]

        resp = client.post("/payments/webhook/", json={
            "event_id": "evt_fail_001",
            "event_type": "payment.updated",
            "payment_id": pay_id,
            "status": "FAILED",
        })
        assert resp.status_code == 200


class TestWebhookIdempotency:
    def test_duplicate_webhook_is_idempotent(
        self, client, user_headers, sample_centre_test, db
    ):
        """Core idempotency test: send the same event 3 times, verify exactly one processing."""
        booking_id, pay_id = _setup_booking_and_payment(
            client, user_headers, sample_centre_test, db
        )

        webhook_payload = {
            "event_id": "evt_idempotent_001",
            "event_type": "payment.updated",
            "payment_id": pay_id,
            "status": "SUCCESS",
        }

        # Send #1
        resp1 = client.post("/payments/webhook/", json=webhook_payload)
        assert resp1.status_code == 200

        # Send #2 — exact same event
        resp2 = client.post("/payments/webhook/", json=webhook_payload)
        assert resp2.status_code == 200
        assert "already processed" in resp2.get_json()["message"].lower()

        # Send #3 — exact same event again
        resp3 = client.post("/payments/webhook/", json=webhook_payload)
        assert resp3.status_code == 200
        assert "already processed" in resp3.get_json()["message"].lower()

        # Verify: only ONE webhook event record exists
        events = WebhookEvent.query.filter_by(event_id="evt_idempotent_001").all()
        assert len(events) == 1

        # Verify: booking state is consistent
        booking = db.session.get(Booking, booking_id)
        assert booking.status == Booking.STATUS_CONFIRMED

    def test_different_events_are_processed_independently(
        self, client, user_headers, sample_centre_test, db
    ):
        """Two different event_ids should both be processed."""
        booking_id, pay_id = _setup_booking_and_payment(
            client, user_headers, sample_centre_test, db
        )

        resp1 = client.post("/payments/webhook/", json={
            "event_id": "evt_a",
            "event_type": "payment.updated",
            "payment_id": pay_id,
            "status": "SUCCESS",
        })
        assert resp1.status_code == 200

        resp2 = client.post("/payments/webhook/", json={
            "event_id": "evt_b",
            "event_type": "payment.updated",
            "payment_id": pay_id,
            "status": "SUCCESS",
        })
        assert resp2.status_code == 200

        events = WebhookEvent.query.filter(
            WebhookEvent.event_id.in_(["evt_a", "evt_b"])
        ).all()
        assert len(events) == 2


class TestWebhookEdgeCases:
    def test_unknown_payment_id(self, client, db):
        resp = client.post("/payments/webhook/", json={
            "event_id": "evt_unknown",
            "event_type": "payment.updated",
            "payment_id": "pay_nonexistent",
            "status": "SUCCESS",
        })
        assert resp.status_code == 404

    def test_malformed_payload(self, client, db):
        resp = client.post("/payments/webhook/", json={
            "event_id": "evt_bad",
        })
        assert resp.status_code == 400

    def test_invalid_status(self, client, db):
        resp = client.post("/payments/webhook/", json={
            "event_id": "evt_invalid",
            "event_type": "payment.updated",
            "payment_id": "pay_123",
            "status": "INVALID",
        })
        assert resp.status_code == 400

    def test_empty_body(self, client, db):
        resp = client.post(
            "/payments/webhook/",
            data="not json",
            content_type="text/plain",
        )
        assert resp.status_code == 400

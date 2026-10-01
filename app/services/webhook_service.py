from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.models.webhook_event import WebhookEvent
from app.utils.errors import APIError


VALID_WEBHOOK_STATUSES = {"SUCCESS", "FAILED"}


def process_webhook(payload: dict) -> dict:
    """Process a payment webhook idempotently.

    Strategy:
    1. Validate the incoming payload.
    2. Try to INSERT the event_id into webhook_events.
    3. If the INSERT violates the UNIQUE constraint, this event was already
       processed — return a safe acknowledgement without re-running logic.
    4. Otherwise, update payment + booking inside the same transaction.

    Concurrency safety:
    - Two identical webhook requests arriving at nearly the same time will
      race to INSERT the event_id.  Only one can succeed due to the UNIQUE
      constraint; the other gets an IntegrityError and returns early.
    - This guarantees exactly-once processing at the database level.
    """
    # --- validate payload ---
    event_id = payload.get("event_id")
    event_type = payload.get("event_type")
    payment_id = payload.get("payment_id")
    status = payload.get("status")

    if not all([event_id, event_type, payment_id, status]):
        raise APIError("Missing required webhook fields: event_id, event_type, payment_id, status", 400)

    if status not in VALID_WEBHOOK_STATUSES:
        raise APIError(f"Invalid payment status: {status}. Must be one of {VALID_WEBHOOK_STATUSES}", 400)

    # --- idempotency: try to register event ---
    webhook_event = WebhookEvent(
        event_id=event_id,
        event_type=event_type,
        payload=payload,
    )

    try:
        db.session.add(webhook_event)
        # Flush to hit the UNIQUE constraint NOW, inside the current txn
        db.session.flush()
    except IntegrityError:
        # Duplicate event — already processed
        db.session.rollback()
        return {"message": "Event already processed", "event_id": event_id}

    # --- find payment ---
    payment = Payment.query.filter_by(provider_payment_id=payment_id).first()
    if not payment:
        # Mark event as processed even though payment wasn't found,
        # so retries don't keep trying
        webhook_event.processed_at = datetime.now(timezone.utc)
        db.session.commit()
        raise APIError(f"Payment not found: {payment_id}", 404)

    # --- update payment + booking ---
    booking = payment.booking

    if status == "SUCCESS":
        payment.status = Payment.STATUS_SUCCESS
        if booking.can_transition_to(Booking.STATUS_CONFIRMED):
            booking.status = Booking.STATUS_CONFIRMED
    elif status == "FAILED":
        payment.status = Payment.STATUS_FAILED
        if booking.can_transition_to(Booking.STATUS_FAILED):
            booking.status = Booking.STATUS_FAILED

    webhook_event.processed_at = datetime.now(timezone.utc)
    db.session.commit()

    return {
        "message": "Webhook processed successfully",
        "event_id": event_id,
        "payment_status": payment.status,
        "booking_status": booking.status,
    }

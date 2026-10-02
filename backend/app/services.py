import uuid
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from app.models import db, User, Booking, CentreTest, Payment, WebhookEvent
from app.auth import hash_password, check_password, generate_token
from app.errors import APIError


# Auth

def signup_user(name, email, password):
    if not name or not email or not password:
        raise APIError("Name, email, and password are required", 400)
    if len(password) < 6:
        raise APIError("Password must be at least 6 characters", 400)
    if User.query.filter_by(email=email).first():
        raise APIError("Email already registered", 409)
    user = User(name=name.strip(), email=email.strip().lower(),
                password_hash=hash_password(password))
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def login_user(email, password):
    if not email or not password:
        raise APIError("Email and password are required", 400)
    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not check_password(password, user.password_hash):
        raise APIError("Invalid email or password", 401)
    return {"token": generate_token(user.id), "user": user.to_dict()}


# Bookings

def create_booking(user_id, centre_test_id, appointment_datetime_str):
    centre_test = db.session.get(CentreTest, centre_test_id)
    if not centre_test:
        raise APIError("Centre-test combination not found", 404)
    try:
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)
    except (ValueError, TypeError):
        raise APIError("Invalid appointment datetime format. Use ISO 8601.", 400)
    if appointment_dt.tzinfo is None:
        appointment_dt = appointment_dt.replace(tzinfo=timezone.utc)
    if appointment_dt <= datetime.now(timezone.utc):
        raise APIError("Appointment datetime must be in the future", 400)

    # price always comes from DB, never from the client
    booking = Booking(user_id=user_id, centre_test_id=centre_test_id,
                      appointment_datetime=appointment_dt, amount=centre_test.price,
                      status=Booking.STATUS_PENDING)
    db.session.add(booking)
    db.session.commit()
    return booking.to_dict()


def get_user_bookings(user_id):
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return [b.to_dict() for b in bookings]


def get_booking(booking_id, user_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)
    return booking.to_dict()


def cancel_booking(booking_id, user_id):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)
    if not booking.can_transition_to(Booking.STATUS_CANCELLED):
        raise APIError(f"Cannot cancel booking with status '{booking.status}'", 409)
    booking.status = Booking.STATUS_CANCELLED
    db.session.commit()
    return booking.to_dict()


# Payments

def create_payment(booking_id, user_id, simulate_failure=False):
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)
    if booking.status != Booking.STATUS_PENDING:
        raise APIError(f"Booking is not payable (current status: {booking.status})", 409)

    # don't allow paying twice
    existing = Payment.query.filter_by(booking_id=booking_id, status=Payment.STATUS_SUCCESS).first()
    if existing:
        raise APIError("Booking already has a successful payment", 409)

    provider_payment_id = f"pay_{uuid.uuid4().hex[:12]}"
    if simulate_failure:
        payment_status, booking_status = Payment.STATUS_FAILED, Booking.STATUS_FAILED
    else:
        payment_status, booking_status = Payment.STATUS_SUCCESS, Booking.STATUS_CONFIRMED

    # payment + booking update in one transaction
    payment = Payment(booking_id=booking_id, provider_payment_id=provider_payment_id,
                      amount=booking.amount, status=payment_status)
    booking.status = booking_status
    db.session.add(payment)
    db.session.commit()
    return payment.to_dict()


# Webhook processing (idempotent)

VALID_WEBHOOK_STATUSES = {"SUCCESS", "FAILED"}


def process_webhook(payload):
    """Process a payment webhook. Uses the webhook_events table with a UNIQUE
    constraint on event_id to make sure we only process each event once,
    even if the provider sends it multiple times."""

    event_id = payload.get("event_id")
    event_type = payload.get("event_type")
    payment_id = payload.get("payment_id")
    status = payload.get("status")

    if not all([event_id, event_type, payment_id, status]):
        raise APIError("Missing required webhook fields: event_id, event_type, payment_id, status", 400)
    if status not in VALID_WEBHOOK_STATUSES:
        raise APIError(f"Invalid payment status: {status}. Must be one of {VALID_WEBHOOK_STATUSES}", 400)

    # try to record this event — if it already exists, the UNIQUE constraint
    # will cause an IntegrityError and we know it's a duplicate
    webhook_event = WebhookEvent(event_id=event_id, event_type=event_type, payload=payload)
    try:
        db.session.add(webhook_event)
        db.session.flush()
    except IntegrityError:
        db.session.rollback()
        return {"message": "Event already processed", "event_id": event_id}

    payment = Payment.query.filter_by(provider_payment_id=payment_id).first()
    if not payment:
        webhook_event.processed_at = datetime.now(timezone.utc)
        db.session.commit()
        raise APIError(f"Payment not found: {payment_id}", 404)

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
    return {"message": "Webhook processed successfully", "event_id": event_id,
            "payment_status": payment.status, "booking_status": booking.status}

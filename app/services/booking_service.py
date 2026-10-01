from datetime import datetime, timezone
from app.extensions import db
from app.models.booking import Booking
from app.models.diagnostic_test import CentreTest
from app.utils.errors import APIError


def create_booking(user_id: int, centre_test_id: int, appointment_datetime_str: str) -> dict:
    """Create a new booking.

    Price is ALWAYS read from the database — never trusted from the client.
    """
    # Validate centre_test exists
    centre_test = db.session.get(CentreTest, centre_test_id)
    if not centre_test:
        raise APIError("Centre-test combination not found", 404)

    # Parse and validate appointment datetime
    try:
        appointment_dt = datetime.fromisoformat(appointment_datetime_str)
    except (ValueError, TypeError):
        raise APIError("Invalid appointment datetime format. Use ISO 8601.", 400)

    if appointment_dt.tzinfo is None:
        appointment_dt = appointment_dt.replace(tzinfo=timezone.utc)

    if appointment_dt <= datetime.now(timezone.utc):
        raise APIError("Appointment datetime must be in the future", 400)

    # Server-side price from DB — critical security rule
    amount = centre_test.price

    booking = Booking(
        user_id=user_id,
        centre_test_id=centre_test_id,
        appointment_datetime=appointment_dt,
        amount=amount,
        status=Booking.STATUS_PENDING,
    )
    db.session.add(booking)
    db.session.commit()
    return booking.to_dict()


def get_user_bookings(user_id: int) -> list:
    """Return all bookings for a specific user."""
    bookings = Booking.query.filter_by(user_id=user_id).order_by(Booking.created_at.desc()).all()
    return [b.to_dict() for b in bookings]


def get_booking(booking_id: int, user_id: int) -> dict:
    """Get a single booking, enforcing ownership."""
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)
    return booking.to_dict()


def cancel_booking(booking_id: int, user_id: int) -> dict:
    """Cancel a booking, enforcing ownership and state machine rules."""
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)

    if not booking.can_transition_to(Booking.STATUS_CANCELLED):
        raise APIError(
            f"Cannot cancel booking with status '{booking.status}'", 409
        )

    booking.status = Booking.STATUS_CANCELLED
    db.session.commit()
    return booking.to_dict()

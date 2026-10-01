import uuid
from app.extensions import db
from app.models.booking import Booking
from app.models.payment import Payment
from app.utils.errors import APIError


def create_payment(booking_id: int, user_id: int, simulate_failure: bool = False) -> dict:
    """Process a simulated payment for a booking.

    The entire operation (create payment + update booking) runs inside
    a single database transaction for consistency.

    Args:
        booking_id: The booking to pay for.
        user_id: The authenticated user — must own the booking.
        simulate_failure: If True, force the payment to fail (useful for tests).
    """
    booking = db.session.get(Booking, booking_id)
    if not booking:
        raise APIError("Booking not found", 404)
    if booking.user_id != user_id:
        raise APIError("Access denied", 403)

    # Only PENDING bookings can be paid
    if booking.status != Booking.STATUS_PENDING:
        raise APIError(
            f"Booking is not payable (current status: {booking.status})", 409
        )

    # Check for existing successful payment — prevent duplicate payment
    existing_payment = Payment.query.filter_by(
        booking_id=booking_id, status=Payment.STATUS_SUCCESS
    ).first()
    if existing_payment:
        raise APIError("Booking already has a successful payment", 409)

    # Simulate payment result
    provider_payment_id = f"pay_{uuid.uuid4().hex[:12]}"

    if simulate_failure:
        payment_status = Payment.STATUS_FAILED
        booking_status = Booking.STATUS_FAILED
    else:
        payment_status = Payment.STATUS_SUCCESS
        booking_status = Booking.STATUS_CONFIRMED

    # Create payment and update booking atomically
    payment = Payment(
        booking_id=booking_id,
        provider_payment_id=provider_payment_id,
        amount=booking.amount,
        status=payment_status,
    )
    booking.status = booking_status

    db.session.add(payment)
    db.session.commit()

    return payment.to_dict()

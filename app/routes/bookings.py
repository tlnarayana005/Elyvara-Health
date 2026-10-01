from flask import Blueprint, request, jsonify, g
from app.utils.auth import login_required
from app.services.booking_service import (
    create_booking,
    get_user_bookings,
    get_booking,
    cancel_booking,
)

bookings_bp = Blueprint("bookings", __name__)


@bookings_bp.route("/", methods=["POST"])
@login_required
def create():
    """Book a diagnostic test.  Price is determined server-side."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    centre_test_id = data.get("centre_test_id")
    appointment_datetime = data.get("appointment_datetime")

    if not centre_test_id or not appointment_datetime:
        return jsonify({"error": "centre_test_id and appointment_datetime are required"}), 400

    result = create_booking(
        user_id=g.current_user.id,
        centre_test_id=centre_test_id,
        appointment_datetime_str=appointment_datetime,
    )
    return jsonify(result), 201


@bookings_bp.route("/", methods=["GET"])
@login_required
def list_bookings():
    """List the current user's bookings."""
    bookings = get_user_bookings(g.current_user.id)
    return jsonify(bookings), 200


@bookings_bp.route("/<int:booking_id>", methods=["GET"])
@login_required
def get_one(booking_id):
    """Get a single booking (must be owned by current user)."""
    result = get_booking(booking_id, g.current_user.id)
    return jsonify(result), 200


@bookings_bp.route("/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel(booking_id):
    """Cancel a booking (must be owned by current user)."""
    result = cancel_booking(booking_id, g.current_user.id)
    return jsonify(result), 200

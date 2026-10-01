from flask import Blueprint, request, jsonify, g
from app.utils.auth import login_required
from app.services.payment_service import create_payment
from app.services.webhook_service import process_webhook

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/", methods=["POST"])
@login_required
def pay():
    """Create a simulated payment for a booking."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "booking_id is required"}), 400

    # Allow tests to force a failure via `simulate_failure` flag
    simulate_failure = data.get("simulate_failure", False)

    result = create_payment(
        booking_id=booking_id,
        user_id=g.current_user.id,
        simulate_failure=simulate_failure,
    )
    return jsonify(result), 201


@payments_bp.route("/webhook/", methods=["POST"])
def webhook():
    """Receive a payment webhook from the simulated provider.

    No JWT required — webhooks come from external systems.
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    result = process_webhook(data)
    return jsonify(result), 200

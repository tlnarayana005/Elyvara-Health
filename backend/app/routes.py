from flask import Blueprint, request, jsonify, g
from app.models import db, DiagnosticCentre, DiagnosticTest, CentreTest
from app.auth import login_required, admin_required
from app.services import (
    signup_user, login_user,
    create_booking, get_user_bookings, get_booking, cancel_booking,
    create_payment, process_webhook,
)
from app.errors import APIError

api = Blueprint("api", __name__)


# Auth

@api.route("/auth/signup", methods=["POST"])
def signup():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    result = signup_user(data.get("name", ""), data.get("email", ""), data.get("password", ""))
    return jsonify({"message": "User created successfully", "user": result}), 201


@api.route("/auth/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    result = login_user(data.get("email", ""), data.get("password", ""))
    return jsonify(result), 200


# Centres

@api.route("/centres/", methods=["GET"])
@login_required
def list_centres():
    centres = DiagnosticCentre.query.order_by(DiagnosticCentre.name).all()
    return jsonify([c.to_dict() for c in centres]), 200


@api.route("/centres/<int:centre_id>", methods=["GET"])
@login_required
def get_centre(centre_id):
    centre = db.session.get(DiagnosticCentre, centre_id)
    if not centre:
        raise APIError("Centre not found", 404)
    return jsonify(centre.to_dict()), 200


@api.route("/centres/", methods=["POST"])
@login_required
@admin_required
def create_centre():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    name = data.get("name", "").strip()
    location = data.get("location", "").strip()
    if not name or not location:
        raise APIError("Name and location are required", 400)
    centre = DiagnosticCentre(name=name, location=location)
    db.session.add(centre)
    db.session.commit()
    return jsonify(centre.to_dict()), 201


@api.route("/centres/<int:centre_id>", methods=["PATCH"])
@login_required
@admin_required
def update_centre(centre_id):
    centre = db.session.get(DiagnosticCentre, centre_id)
    if not centre:
        raise APIError("Centre not found", 404)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    if "name" in data:
        centre.name = data["name"].strip()
    if "location" in data:
        centre.location = data["location"].strip()
    db.session.commit()
    return jsonify(centre.to_dict()), 200


@api.route("/centres/<int:centre_id>/tests", methods=["GET"])
@login_required
def get_centre_tests(centre_id):
    centre = db.session.get(DiagnosticCentre, centre_id)
    if not centre:
        raise APIError("Centre not found", 404)
    centre_tests = CentreTest.query.filter_by(centre_id=centre_id).all()
    return jsonify([ct.to_dict() for ct in centre_tests]), 200


# Tests

@api.route("/tests/", methods=["GET"])
@login_required
def list_tests():
    tests = DiagnosticTest.query.order_by(DiagnosticTest.name).all()
    return jsonify([t.to_dict() for t in tests]), 200


@api.route("/tests/<int:test_id>", methods=["GET"])
@login_required
def get_test(test_id):
    test = db.session.get(DiagnosticTest, test_id)
    if not test:
        raise APIError("Test not found", 404)
    return jsonify(test.to_dict()), 200


@api.route("/tests/", methods=["POST"])
@login_required
@admin_required
def create_test():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    name = data.get("name", "").strip()
    if not name:
        raise APIError("Test name is required", 400)
    test = DiagnosticTest(name=name, description=data.get("description", "").strip() or None)
    db.session.add(test)
    db.session.commit()
    return jsonify(test.to_dict()), 201


@api.route("/tests/<int:test_id>", methods=["PATCH"])
@login_required
@admin_required
def update_test(test_id):
    test = db.session.get(DiagnosticTest, test_id)
    if not test:
        raise APIError("Test not found", 404)
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    if "name" in data:
        test.name = data["name"].strip()
    if "description" in data:
        test.description = data["description"].strip() or None
    db.session.commit()
    return jsonify(test.to_dict()), 200


@api.route("/tests/centre-tests", methods=["POST"])
@login_required
@admin_required
def create_centre_test():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    centre_id = data.get("centre_id")
    test_id = data.get("test_id")
    price = data.get("price")
    if not all([centre_id, test_id, price]):
        raise APIError("centre_id, test_id, and price are required", 400)
    if float(price) <= 0:
        raise APIError("Price must be positive", 400)
    if not db.session.get(DiagnosticCentre, centre_id):
        raise APIError("Centre not found", 404)
    if not db.session.get(DiagnosticTest, test_id):
        raise APIError("Test not found", 404)
    existing = CentreTest.query.filter_by(centre_id=centre_id, test_id=test_id).first()
    if existing:
        raise APIError("This centre-test combination already exists", 409)
    ct = CentreTest(centre_id=centre_id, test_id=test_id, price=price)
    db.session.add(ct)
    db.session.commit()
    return jsonify(ct.to_dict()), 201


# Bookings

@api.route("/bookings/", methods=["POST"])
@login_required
def create_booking_route():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    centre_test_id = data.get("centre_test_id")
    appointment_datetime = data.get("appointment_datetime")
    if not centre_test_id or not appointment_datetime:
        return jsonify({"error": "centre_test_id and appointment_datetime are required"}), 400
    result = create_booking(g.current_user.id, centre_test_id, appointment_datetime)
    return jsonify(result), 201


@api.route("/bookings/", methods=["GET"])
@login_required
def list_bookings():
    return jsonify(get_user_bookings(g.current_user.id)), 200


@api.route("/bookings/<int:booking_id>", methods=["GET"])
@login_required
def get_one_booking(booking_id):
    return jsonify(get_booking(booking_id, g.current_user.id)), 200


@api.route("/bookings/<int:booking_id>/cancel", methods=["POST"])
@login_required
def cancel_booking_route(booking_id):
    return jsonify(cancel_booking(booking_id, g.current_user.id)), 200


# Payments

@api.route("/payments/", methods=["POST"])
@login_required
def pay():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    booking_id = data.get("booking_id")
    if not booking_id:
        return jsonify({"error": "booking_id is required"}), 400
    simulate_failure = data.get("simulate_failure", False)
    result = create_payment(booking_id, g.current_user.id, simulate_failure)
    return jsonify(result), 201


@api.route("/payments/webhook/", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400
    return jsonify(process_webhook(data)), 200

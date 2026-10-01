from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models.diagnostic_test import DiagnosticTest, CentreTest
from app.models.diagnostic_centre import DiagnosticCentre
from app.utils.auth import login_required, admin_required
from app.utils.errors import APIError

tests_bp = Blueprint("tests", __name__)


@tests_bp.route("/", methods=["GET"])
@login_required
def list_tests():
    """List all diagnostic tests."""
    tests = DiagnosticTest.query.order_by(DiagnosticTest.name).all()
    return jsonify([t.to_dict() for t in tests]), 200


@tests_bp.route("/<int:test_id>", methods=["GET"])
@login_required
def get_test(test_id):
    """Get a single diagnostic test."""
    test = db.session.get(DiagnosticTest, test_id)
    if not test:
        raise APIError("Test not found", 404)
    return jsonify(test.to_dict()), 200


@tests_bp.route("/", methods=["POST"])
@login_required
@admin_required
def create_test():
    """Create a new diagnostic test (admin only)."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    name = data.get("name", "").strip()
    if not name:
        raise APIError("Test name is required", 400)

    test = DiagnosticTest(
        name=name,
        description=data.get("description", "").strip() or None,
    )
    db.session.add(test)
    db.session.commit()
    return jsonify(test.to_dict()), 201


@tests_bp.route("/<int:test_id>", methods=["PATCH"])
@login_required
@admin_required
def update_test(test_id):
    """Update a diagnostic test (admin only)."""
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


# --- Centre-Test association management (admin) ---

@tests_bp.route("/centre-tests", methods=["POST"])
@login_required
@admin_required
def create_centre_test():
    """Associate a test with a centre at a given price (admin only)."""
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

    # Validate foreign keys exist
    if not db.session.get(DiagnosticCentre, centre_id):
        raise APIError("Centre not found", 404)
    if not db.session.get(DiagnosticTest, test_id):
        raise APIError("Test not found", 404)

    # Check for duplicate
    existing = CentreTest.query.filter_by(centre_id=centre_id, test_id=test_id).first()
    if existing:
        raise APIError("This centre-test combination already exists", 409)

    ct = CentreTest(centre_id=centre_id, test_id=test_id, price=price)
    db.session.add(ct)
    db.session.commit()
    return jsonify(ct.to_dict()), 201

from flask import Blueprint, request, jsonify, g
from app.extensions import db
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import CentreTest
from app.utils.auth import login_required, admin_required
from app.utils.errors import APIError

centres_bp = Blueprint("centres", __name__)


@centres_bp.route("/", methods=["GET"])
@login_required
def list_centres():
    """List all diagnostic centres."""
    centres = DiagnosticCentre.query.order_by(DiagnosticCentre.name).all()
    return jsonify([c.to_dict() for c in centres]), 200


@centres_bp.route("/<int:centre_id>", methods=["GET"])
@login_required
def get_centre(centre_id):
    """Get a single diagnostic centre."""
    centre = db.session.get(DiagnosticCentre, centre_id)
    if not centre:
        raise APIError("Centre not found", 404)
    return jsonify(centre.to_dict()), 200


@centres_bp.route("/", methods=["POST"])
@login_required
@admin_required
def create_centre():
    """Create a new diagnostic centre (admin only)."""
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


@centres_bp.route("/<int:centre_id>", methods=["PATCH"])
@login_required
@admin_required
def update_centre(centre_id):
    """Update a diagnostic centre (admin only)."""
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


@centres_bp.route("/<int:centre_id>/tests", methods=["GET"])
@login_required
def get_centre_tests(centre_id):
    """List all tests offered by a specific centre, with prices."""
    centre = db.session.get(DiagnosticCentre, centre_id)
    if not centre:
        raise APIError("Centre not found", 404)

    centre_tests = CentreTest.query.filter_by(centre_id=centre_id).all()
    return jsonify([ct.to_dict() for ct in centre_tests]), 200

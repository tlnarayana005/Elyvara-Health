from flask import Blueprint, request, jsonify
from app.services.auth_service import signup_user, login_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    """Register a new user."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    result = signup_user(
        name=data.get("name", ""),
        email=data.get("email", ""),
        password=data.get("password", ""),
    )
    return jsonify({"message": "User created successfully", "user": result}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate and return a JWT."""
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "Request body must be JSON"}), 400

    result = login_user(
        email=data.get("email", ""),
        password=data.get("password", ""),
    )
    return jsonify(result), 200

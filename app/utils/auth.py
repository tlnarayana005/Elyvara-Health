import bcrypt
import jwt
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import request, jsonify, current_app, g

from app.extensions import db
from app.models.user import User


def hash_password(password: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, password_hash: str) -> bool:
    """Verify a plaintext password against a bcrypt hash."""
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def generate_token(user_id: int) -> str:
    """Create a JWT for the given user."""
    payload = {
        "user_id": user_id,
        "exp": datetime.now(timezone.utc)
        + timedelta(hours=current_app.config["JWT_EXPIRY_HOURS"]),
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(
        payload,
        current_app.config["JWT_SECRET_KEY"],
        algorithm=current_app.config["JWT_ALGORITHM"],
    )


def decode_token(token: str) -> dict:
    """Decode and validate a JWT. Raises on invalid/expired tokens."""
    return jwt.decode(
        token,
        current_app.config["JWT_SECRET_KEY"],
        algorithms=[current_app.config["JWT_ALGORITHM"]],
    )


# --------------- decorators ---------------

def login_required(f):
    """Decorator that enforces JWT authentication.

    Sets g.current_user on success.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid authorization header"}), 401

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401

        user = db.session.get(User, payload["user_id"])
        if user is None:
            return jsonify({"error": "User not found"}), 401

        g.current_user = user
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Decorator that enforces admin-level access.

    Must be used *after* @login_required so that g.current_user exists.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({"error": "Admin access required"}), 403
        return f(*args, **kwargs)
    return decorated

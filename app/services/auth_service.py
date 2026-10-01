from app.extensions import db
from app.models.user import User
from app.utils.auth import hash_password, check_password, generate_token
from app.utils.errors import APIError


def signup_user(name: str, email: str, password: str) -> dict:
    """Register a new user. Returns safe user dict."""
    if not name or not email or not password:
        raise APIError("Name, email, and password are required", 400)

    if len(password) < 6:
        raise APIError("Password must be at least 6 characters", 400)

    existing = User.query.filter_by(email=email).first()
    if existing:
        raise APIError("Email already registered", 409)

    user = User(
        name=name.strip(),
        email=email.strip().lower(),
        password_hash=hash_password(password),
    )
    db.session.add(user)
    db.session.commit()
    return user.to_dict()


def login_user(email: str, password: str) -> dict:
    """Authenticate user. Returns JWT and safe user dict."""
    if not email or not password:
        raise APIError("Email and password are required", 400)

    user = User.query.filter_by(email=email.strip().lower()).first()
    if not user or not check_password(password, user.password_hash):
        raise APIError("Invalid email or password", 401)

    token = generate_token(user.id)
    return {"token": token, "user": user.to_dict()}

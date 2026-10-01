import pytest
from app import create_app
from app.config import TestConfig
from app.extensions import db as _db
from app.models import (
    User, DiagnosticCentre, DiagnosticTest, CentreTest,
    Booking, Payment, WebhookEvent,
)
from app.utils.auth import hash_password, generate_token


@pytest.fixture(scope="session")
def app():
    """Create the Flask application for the test session."""
    app = create_app(config_class=TestConfig)
    return app


@pytest.fixture(scope="function")
def db(app):
    """Provide a clean database for each test function."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.rollback()
        _db.drop_all()


@pytest.fixture
def client(app, db):
    """Flask test client."""
    return app.test_client()


# ----------- helper fixtures -----------

@pytest.fixture
def admin_user(db):
    """Create and return an admin user."""
    user = User(
        name="Admin",
        email="admin@test.com",
        password_hash=hash_password("admin123"),
        is_admin=True,
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def normal_user(db):
    """Create and return a normal user."""
    user = User(
        name="Alice",
        email="alice@test.com",
        password_hash=hash_password("alice123"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def other_user(db):
    """Second normal user for cross-user tests."""
    user = User(
        name="Bob",
        email="bob@test.com",
        password_hash=hash_password("bob12345"),
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def admin_headers(app, admin_user):
    """Auth headers for the admin user."""
    with app.app_context():
        token = generate_token(admin_user.id)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def user_headers(app, normal_user):
    """Auth headers for the normal user."""
    with app.app_context():
        token = generate_token(normal_user.id)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def other_user_headers(app, other_user):
    """Auth headers for the other user."""
    with app.app_context():
        token = generate_token(other_user.id)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


@pytest.fixture
def sample_centre(db):
    """Create a sample diagnostic centre."""
    centre = DiagnosticCentre(name="Test Centre", location="Test City")
    db.session.add(centre)
    db.session.commit()
    return centre


@pytest.fixture
def sample_test(db):
    """Create a sample diagnostic test."""
    test = DiagnosticTest(name="Blood Test", description="CBC analysis")
    db.session.add(test)
    db.session.commit()
    return test


@pytest.fixture
def sample_centre_test(db, sample_centre, sample_test):
    """Create a centre-test relationship with a known price."""
    ct = CentreTest(
        centre_id=sample_centre.id,
        test_id=sample_test.id,
        price=500.00,
    )
    db.session.add(ct)
    db.session.commit()
    return ct

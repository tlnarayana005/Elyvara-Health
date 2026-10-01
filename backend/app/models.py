"""All SQLAlchemy models for the EVE Healthcare platform."""
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


# ── User ──────────────────────────────────────────────────

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    bookings = db.relationship("Booking", back_populates="user", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "email": self.email,
            "is_admin": self.is_admin,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Diagnostic Centre ────────────────────────────────────

class DiagnosticCentre(db.Model):
    __tablename__ = "diagnostic_centres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    centre_tests = db.relationship("CentreTest", back_populates="centre", lazy="dynamic")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "location": self.location,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Diagnostic Test + CentreTest (many-to-many with price) ─

class DiagnosticTest(db.Model):
    __tablename__ = "diagnostic_tests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    centre_tests = db.relationship("CentreTest", back_populates="test", lazy="dynamic")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "description": self.description,
                "created_at": self.created_at.isoformat()}


class CentreTest(db.Model):
    """Links a centre to a test with a specific price."""
    __tablename__ = "centre_tests"
    __table_args__ = (db.UniqueConstraint("centre_id", "test_id", name="uq_centre_test"),)

    id = db.Column(db.Integer, primary_key=True)
    centre_id = db.Column(db.Integer, db.ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
                          nullable=False, index=True)
    test_id = db.Column(db.Integer, db.ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)

    centre = db.relationship("DiagnosticCentre", back_populates="centre_tests")
    test = db.relationship("DiagnosticTest", back_populates="centre_tests")

    def to_dict(self):
        return {
            "id": self.id, "centre_id": self.centre_id, "test_id": self.test_id,
            "price": float(self.price),
            "centre_name": self.centre.name if self.centre else None,
            "test_name": self.test.name if self.test else None,
        }


# ── Booking (with state machine) ─────────────────────────

class Booking(db.Model):
    __tablename__ = "bookings"

    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    VALID_TRANSITIONS = {
        STATUS_PENDING: {STATUS_CONFIRMED, STATUS_FAILED, STATUS_CANCELLED},
        STATUS_CONFIRMED: {STATUS_CANCELLED},
        STATUS_FAILED: {STATUS_CANCELLED},
        STATUS_CANCELLED: set(),
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    centre_test_id = db.Column(db.Integer, db.ForeignKey("centre_tests.id", ondelete="CASCADE"),
                               nullable=False, index=True)
    appointment_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    user = db.relationship("User", back_populates="bookings")
    centre_test = db.relationship("CentreTest")
    payments = db.relationship("Payment", back_populates="booking", lazy="dynamic")

    def can_transition_to(self, new_status):
        return new_status in self.VALID_TRANSITIONS.get(self.status, set())

    def to_dict(self):
        return {
            "id": self.id, "user_id": self.user_id,
            "centre_test_id": self.centre_test_id,
            "appointment_datetime": self.appointment_datetime.isoformat(),
            "amount": float(self.amount), "status": self.status,
            "centre_name": self.centre_test.centre.name if self.centre_test else None,
            "test_name": self.centre_test.test.name if self.centre_test else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Payment ───────────────────────────────────────────────

class Payment(db.Model):
    __tablename__ = "payments"

    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey("bookings.id", ondelete="CASCADE"),
                           nullable=False, index=True)
    provider_payment_id = db.Column(db.String(255), nullable=True, unique=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    booking = db.relationship("Booking", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id, "booking_id": self.booking_id,
            "provider_payment_id": self.provider_payment_id,
            "amount": float(self.amount), "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# ── Webhook Event (idempotency) ──────────────────────────

class WebhookEvent(db.Model):
    """Stores processed webhook events. The UNIQUE constraint on event_id
    ensures exactly-once processing even under concurrent requests."""
    __tablename__ = "webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

from datetime import datetime, timezone
from app.extensions import db


class Booking(db.Model):
    __tablename__ = "bookings"

    # Valid status values
    STATUS_PENDING = "PENDING"
    STATUS_CONFIRMED = "CONFIRMED"
    STATUS_FAILED = "FAILED"
    STATUS_CANCELLED = "CANCELLED"

    # Allowed state transitions — centralized rule
    VALID_TRANSITIONS = {
        STATUS_PENDING: {STATUS_CONFIRMED, STATUS_FAILED, STATUS_CANCELLED},
        STATUS_CONFIRMED: {STATUS_CANCELLED},
        STATUS_FAILED: {STATUS_CANCELLED},
        STATUS_CANCELLED: set(),  # terminal state
    }

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    centre_test_id = db.Column(
        db.Integer,
        db.ForeignKey("centre_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    appointment_datetime = db.Column(db.DateTime(timezone=True), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=STATUS_PENDING)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user = db.relationship("User", back_populates="bookings")
    centre_test = db.relationship("CentreTest")
    payments = db.relationship("Payment", back_populates="booking", lazy="dynamic")

    def can_transition_to(self, new_status: str) -> bool:
        """Check if transitioning to new_status is allowed."""
        allowed = self.VALID_TRANSITIONS.get(self.status, set())
        return new_status in allowed

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "centre_test_id": self.centre_test_id,
            "appointment_datetime": self.appointment_datetime.isoformat(),
            "amount": float(self.amount),
            "status": self.status,
            "centre_name": (
                self.centre_test.centre.name if self.centre_test else None
            ),
            "test_name": (
                self.centre_test.test.name if self.centre_test else None
            ),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

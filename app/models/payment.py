from datetime import datetime, timezone
from app.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    STATUS_PENDING = "PENDING"
    STATUS_SUCCESS = "SUCCESS"
    STATUS_FAILED = "FAILED"

    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(
        db.Integer,
        db.ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider_payment_id = db.Column(db.String(255), nullable=True, unique=True)
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
    booking = db.relationship("Booking", back_populates="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "booking_id": self.booking_id,
            "provider_payment_id": self.provider_payment_id,
            "amount": float(self.amount),
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

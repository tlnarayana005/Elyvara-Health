from datetime import datetime, timezone
from app.extensions import db


class WebhookEvent(db.Model):
    """Stores processed webhook events for idempotency.

    The UNIQUE constraint on event_id ensures that the same external event
    cannot be processed twice, even under concurrent requests.
    """
    __tablename__ = "webhook_events"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    event_type = db.Column(db.String(100), nullable=False)
    payload = db.Column(db.JSON, nullable=False)
    processed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

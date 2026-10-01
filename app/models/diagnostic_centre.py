from datetime import datetime, timezone
from app.extensions import db


class DiagnosticCentre(db.Model):
    __tablename__ = "diagnostic_centres"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.String(255), nullable=False)
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
    centre_tests = db.relationship(
        "CentreTest", back_populates="centre", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

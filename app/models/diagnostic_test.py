from datetime import datetime, timezone
from app.extensions import db


class DiagnosticTest(db.Model):
    __tablename__ = "diagnostic_tests"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    centre_tests = db.relationship(
        "CentreTest", back_populates="test", lazy="dynamic"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
        }


class CentreTest(db.Model):
    """Association table: links a centre to a test with a specific price."""
    __tablename__ = "centre_tests"
    __table_args__ = (
        db.UniqueConstraint("centre_id", "test_id", name="uq_centre_test"),
    )

    id = db.Column(db.Integer, primary_key=True)
    centre_id = db.Column(
        db.Integer,
        db.ForeignKey("diagnostic_centres.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    test_id = db.Column(
        db.Integer,
        db.ForeignKey("diagnostic_tests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    price = db.Column(db.Numeric(10, 2), nullable=False)

    # Relationships
    centre = db.relationship("DiagnosticCentre", back_populates="centre_tests")
    test = db.relationship("DiagnosticTest", back_populates="centre_tests")

    def to_dict(self):
        return {
            "id": self.id,
            "centre_id": self.centre_id,
            "test_id": self.test_id,
            "price": float(self.price),
            "centre_name": self.centre.name if self.centre else None,
            "test_name": self.test.name if self.test else None,
        }

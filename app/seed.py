"""Seed the database with sample data.

Usage:
    python -m app.seed

This is idempotent — it checks for existing data before inserting.
"""

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.diagnostic_centre import DiagnosticCentre
from app.models.diagnostic_test import DiagnosticTest, CentreTest
from app.utils.auth import hash_password


def seed():
    app = create_app()
    with app.app_context():
        # --- Users ---
        if not User.query.filter_by(email="admin@eve.com").first():
            admin = User(
                name="Admin User",
                email="admin@eve.com",
                password_hash=hash_password("admin123"),
                is_admin=True,
            )
            db.session.add(admin)
            print("Created admin user: admin@eve.com / admin123")

        if not User.query.filter_by(email="alice@example.com").first():
            alice = User(
                name="Alice Johnson",
                email="alice@example.com",
                password_hash=hash_password("alice123"),
            )
            db.session.add(alice)
            print("Created user: alice@example.com / alice123")

        if not User.query.filter_by(email="bob@example.com").first():
            bob = User(
                name="Bob Smith",
                email="bob@example.com",
                password_hash=hash_password("bob12345"),
            )
            db.session.add(bob)
            print("Created user: bob@example.com / bob12345")

        db.session.flush()

        # --- Diagnostic Centres ---
        centres_data = [
            {"name": "HealthFirst Diagnostics", "location": "Mumbai, Maharashtra"},
            {"name": "MedScan Labs", "location": "Delhi, NCR"},
            {"name": "CityHealth Centre", "location": "Bangalore, Karnataka"},
        ]
        centres = {}
        for cd in centres_data:
            existing = DiagnosticCentre.query.filter_by(name=cd["name"]).first()
            if existing:
                centres[cd["name"]] = existing
            else:
                c = DiagnosticCentre(**cd)
                db.session.add(c)
                db.session.flush()
                centres[cd["name"]] = c
                print(f"Created centre: {cd['name']}")

        # --- Diagnostic Tests ---
        tests_data = [
            {"name": "Complete Blood Count", "description": "Full blood panel analysis"},
            {"name": "Lipid Profile", "description": "Cholesterol and triglyceride levels"},
            {"name": "Thyroid Panel", "description": "TSH, T3, T4 hormone levels"},
            {"name": "Liver Function Test", "description": "ALT, AST, bilirubin levels"},
            {"name": "Chest X-Ray", "description": "Standard PA chest radiograph"},
        ]
        tests = {}
        for td in tests_data:
            existing = DiagnosticTest.query.filter_by(name=td["name"]).first()
            if existing:
                tests[td["name"]] = existing
            else:
                t = DiagnosticTest(**td)
                db.session.add(t)
                db.session.flush()
                tests[td["name"]] = t
                print(f"Created test: {td['name']}")

        # --- Centre-Test Relationships with varying prices ---
        ct_data = [
            ("HealthFirst Diagnostics", "Complete Blood Count", 500),
            ("HealthFirst Diagnostics", "Lipid Profile", 800),
            ("HealthFirst Diagnostics", "Thyroid Panel", 1200),
            ("HealthFirst Diagnostics", "Chest X-Ray", 600),
            ("MedScan Labs", "Complete Blood Count", 450),
            ("MedScan Labs", "Lipid Profile", 750),
            ("MedScan Labs", "Liver Function Test", 900),
            ("MedScan Labs", "Chest X-Ray", 550),
            ("CityHealth Centre", "Complete Blood Count", 400),
            ("CityHealth Centre", "Thyroid Panel", 1100),
            ("CityHealth Centre", "Liver Function Test", 850),
        ]
        for centre_name, test_name, price in ct_data:
            c = centres[centre_name]
            t = tests[test_name]
            existing = CentreTest.query.filter_by(
                centre_id=c.id, test_id=t.id
            ).first()
            if not existing:
                ct = CentreTest(centre_id=c.id, test_id=t.id, price=price)
                db.session.add(ct)
                print(f"  {centre_name} - {test_name}: Rs.{price}")

        db.session.commit()
        print("\nSeed completed successfully!")


if __name__ == "__main__":
    seed()

"""Seed sample data into the database. Safe to run multiple times."""
from app import create_app
from app.models import db, User, DiagnosticCentre, DiagnosticTest, CentreTest
from app.auth import hash_password


def seed():
    app = create_app()
    with app.app_context():
        # users
        for name, email, pw, admin in [
            ("Admin User", "admin@eve.com", "admin123", True),
            ("Alice Johnson", "alice@example.com", "alice123", False),
            ("Bob Smith", "bob@example.com", "bob12345", False),
        ]:
            if not User.query.filter_by(email=email).first():
                db.session.add(User(name=name, email=email, password_hash=hash_password(pw), is_admin=admin))
                print(f"Created {'admin' if admin else 'user'}: {email} / {pw}")
        db.session.flush()

        # centres
        centres = {}
        for name, loc in [
            ("HealthFirst Diagnostics", "Mumbai, Maharashtra"),
            ("MedScan Labs", "Delhi, NCR"),
            ("CityHealth Centre", "Bangalore, Karnataka"),
        ]:
            c = DiagnosticCentre.query.filter_by(name=name).first()
            if not c:
                c = DiagnosticCentre(name=name, location=loc)
                db.session.add(c)
                db.session.flush()
                print(f"Created centre: {name}")
            centres[name] = c

        # tests
        tests = {}
        for name, desc in [
            ("Complete Blood Count", "Full blood panel analysis"),
            ("Lipid Profile", "Cholesterol and triglyceride levels"),
            ("Thyroid Panel", "TSH, T3, T4 hormone levels"),
            ("Liver Function Test", "ALT, AST, bilirubin levels"),
            ("Chest X-Ray", "Standard PA chest radiograph"),
        ]:
            t = DiagnosticTest.query.filter_by(name=name).first()
            if not t:
                t = DiagnosticTest(name=name, description=desc)
                db.session.add(t)
                db.session.flush()
                print(f"Created test: {name}")
            tests[name] = t

        # centre-test pricing
        for centre_name, test_name, price in [
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
        ]:
            c, t = centres[centre_name], tests[test_name]
            if not CentreTest.query.filter_by(centre_id=c.id, test_id=t.id).first():
                db.session.add(CentreTest(centre_id=c.id, test_id=t.id, price=price))
                print(f"  {centre_name} - {test_name}: Rs.{price}")

        db.session.commit()
        print("\nDone!")


if __name__ == "__main__":
    seed()

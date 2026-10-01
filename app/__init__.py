from flask import Flask
from app.config import Config
from app.extensions import db


def create_app(config_class=Config):
    """Application factory pattern."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.centres import centres_bp
    from app.routes.tests import tests_bp
    from app.routes.bookings import bookings_bp
    from app.routes.payments import payments_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(centres_bp, url_prefix="/centres")
    app.register_blueprint(tests_bp, url_prefix="/tests")
    app.register_blueprint(bookings_bp, url_prefix="/bookings")
    app.register_blueprint(payments_bp, url_prefix="/payments")

    # Health check
    @app.route("/health")
    def health():
        return {"status": "healthy"}

    # Global error handlers
    from app.utils.errors import register_error_handlers
    register_error_handlers(app)

    return app

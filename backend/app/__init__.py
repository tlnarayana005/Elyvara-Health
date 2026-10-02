from flask import Flask
from flask_cors import CORS
from app.config import Config
from app.models import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    from app.routes import api
    app.register_blueprint(api)

    @app.route("/health")
    def health():
        return {"status": "healthy"}

    from app.errors import register_error_handlers
    register_error_handlers(app)

    return app

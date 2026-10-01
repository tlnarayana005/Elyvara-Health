from flask import jsonify
from sqlalchemy.exc import SQLAlchemyError


class APIError(Exception):
    """Application-level error that maps to an HTTP status code."""

    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def register_error_handlers(app):
    """Register global error handlers on the Flask app."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        return jsonify({"error": error.message}), error.status_code

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({"error": "Unprocessable entity"}), 422

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(SQLAlchemyError)
    def handle_db_error(error):
        # Never expose raw DB errors to clients
        return jsonify({"error": "A database error occurred"}), 500

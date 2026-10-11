from flask import jsonify
from werkzeug.exceptions import HTTPException

from app.extensions import db

# Friendly messages for errors that Flask itself raises.
HTTP_ERROR_MESSAGES = {
    404: "Resource not found",
    405: "Method not allowed for this URL",
}


def register_error_handlers(app):
    """Make every error response a JSON object: {"error": "message"}."""

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        message = HTTP_ERROR_MESSAGES.get(error.code, error.description)
        return jsonify({"error": message}), error.code

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        # Undo any half-finished database work, log details privately,
        # and return a generic message (never a stack trace).
        db.session.rollback()
        app.logger.exception("Unexpected error")
        return jsonify({"error": "Internal server error"}), 500
import os

from flask import Flask

from app.extensions import db


def create_app(test_config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Development database: F:\TaskFlow\instance\taskflow.db
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    # Tests can pass their own settings (e.g. a separate database).
    if test_config is not None:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from app import models  # noqa: F401  (registers the Task model)

    with app.app_context():
        db.create_all()

    from app.errors import register_error_handlers
    from app.routes import bp

    register_error_handlers(app)
    app.register_blueprint(bp)

    return app
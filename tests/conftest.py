import pytest

from app import create_app
from app.extensions import db


@pytest.fixture
def app():
    """A fresh app with its own empty in-memory database for each test."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
    })
    yield app
    with app.app_context():
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """A test client that sends requests to the app without a real server."""
    return app.test_client()
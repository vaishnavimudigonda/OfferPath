import os
import sys
from pathlib import Path
import pytest

# Ensure backend root is in python path
backend_path = Path(__file__).resolve().parent.parent
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from app import create_app
from app.models import db, User
from app.utils.auth_helpers import generate_token


@pytest.fixture
def app(tmp_path):
    """Create and configure an isolated file-backed SQLite database for testing."""
    test_db = tmp_path / "test_offerpath.db"
    app_instance = create_app("testing")
    app_instance.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{test_db}"
    app_instance.config["TESTING"] = True
    
    with app_instance.app_context():
        db.create_all()
        yield app_instance
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test HTTP client."""
    return app.test_client()


@pytest.fixture
def test_user(app):
    """Create a verified test user."""
    with app.app_context():
        user = User(
            username="testuser",
            email="testuser@example.com",
            full_name="Test User",
            target_role="Full Stack Developer"
        )
        user.set_password("Secret123!")
        db.session.add(user)
        db.session.commit()
        user_id = user.id
        return db.session.get(User, user_id)


@pytest.fixture
def auth_headers(app, test_user):
    """Generate authorization headers for test user."""
    with app.app_context():
        token = generate_token(test_user.id)
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

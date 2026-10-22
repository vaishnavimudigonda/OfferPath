from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from app.models import db


class User(db.Model):
    """User account model with secure password hashing."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    target_role = db.Column(db.String(100), nullable=True, default="Software Engineer")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    applications = db.relationship("Application", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    resumes = db.relationship("Resume", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    analyses = db.relationship("Analysis", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    interview_questions = db.relationship("InterviewQuestion", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password: str) -> None:
        """Hash and store the password securely."""
        self.password_hash = generate_password_hash(password, method="scrypt")

    def check_password(self, password: str) -> bool:
        """Verify the password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Return user data without sensitive password hashes."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name or self.username,
            "target_role": self.target_role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<User {self.username} (id={self.id})>"

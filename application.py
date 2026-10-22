from datetime import datetime, date
from app.models import db

VALID_STATUSES = ["Saved", "Applied", "Assessment", "Interview", "Offer", "Rejected"]


class Application(db.Model):
    """Job application tracker model."""
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    company_name = db.Column(db.String(150), nullable=False)
    job_title = db.Column(db.String(150), nullable=False)
    job_description = db.Column(db.Text, nullable=True)
    application_date = db.Column(db.Date, default=date.today, nullable=False)
    job_url = db.Column(db.String(500), nullable=True)
    location = db.Column(db.String(150), nullable=True, default="Remote")
    salary = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), nullable=False, default="Saved", index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    analyses = db.relationship("Analysis", backref="application", cascade="all, delete-orphan", lazy="dynamic")
    interview_questions = db.relationship("InterviewQuestion", backref="application", cascade="all, delete-orphan", lazy="dynamic")

    def to_dict(self) -> dict:
        """Convert application model to a JSON-serializable dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "company_name": self.company_name,
            "job_title": self.job_title,
            "job_description": self.job_description,
            "application_date": self.application_date.isoformat() if self.application_date else None,
            "job_url": self.job_url,
            "location": self.location,
            "salary": self.salary,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def __repr__(self) -> str:
        return f"<Application {self.company_name} - {self.job_title} ({self.status})>"

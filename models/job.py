"""
Job application related models
"""
from datetime import datetime, timezone
from .base import db
from .enums import ApplicationStatus, JobMode


class JobApplication(db.Model):
    """Model for job applications"""
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default=ApplicationStatus.COLLECTED.value, nullable=False)
    last_update = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    url = db.Column(db.String(500))

    # New fields for location and job mode
    office_location = db.Column(db.String(200))  # City, office address
    country = db.Column(db.String(100))  # Country
    job_mode = db.Column(db.String(50), default=JobMode.ON_SITE.value)  # Remote, Hybrid, On-site

    # Relationships
    documents = db.relationship('Document', backref='job_application', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('JobLog', backref='job_application', lazy=True, cascade='all, delete-orphan', order_by='JobLog.created_at.desc()')
    
    @property
    def status_enum(self):
        """Get the status as an enum"""
        return ApplicationStatus(self.status)
    
    @status_enum.setter
    def status_enum(self, value):
        """Set the status from an enum"""
        if isinstance(value, ApplicationStatus):
            self.status = value.value
        else:
            self.status = value

    @property
    def job_mode_enum(self):
        """Get the job mode as an enum"""
        try:
            return JobMode(self.job_mode)
        except ValueError:
            return JobMode.ON_SITE  # Default fallback

    @job_mode_enum.setter
    def job_mode_enum(self, value):
        """Set the job mode from an enum"""
        if isinstance(value, JobMode):
            self.job_mode = value.value
        else:
            self.job_mode = value

    def __repr__(self):
        return f'<JobApplication {self.company} - {self.title}>'


class Document(db.Model):
    """Model for job application documents (CV, cover letters, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # CV, Cover Letter
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f'<Document {self.type} for Job {self.job_id}>'


class JobLog(db.Model):
    """Model for job application logs and status changes"""
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    note = db.Column(db.Text, nullable=False)
    status_change_from = db.Column(db.String(50))  # Previous status if this log represents a status change
    status_change_to = db.Column(db.String(50))    # New status if this log represents a status change

    def __repr__(self):
        return f'<JobLog {self.id}: {self.note[:50]}...>'

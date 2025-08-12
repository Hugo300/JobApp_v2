from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import os

# We'll get db from the app context instead of importing directly
db = SQLAlchemy()

class ApplicationStatus(Enum):
    COLLECTED = "Collected"
    APPLIED = "Applied"
    PROCESS = "Process"
    WAITING_DECISION = "Waiting Decision"
    COMPLETED = "Completed"
    REJECTED = "Rejected"

class TemplateType(Enum):
    DATABASE = "database"
    FILE = "file"

class JobMode(Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))


class MasterTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(20), default=TemplateType.DATABASE.value)
    file_path = db.Column(db.String(500))  # Path to template file if file-based
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def get_content(self):
        """Get template content, either from database or file"""
        if self.template_type == TemplateType.FILE.value and self.file_path:
            try:
                # Validate file path to prevent directory traversal
                if '..' in self.file_path or self.file_path.startswith('/'):
                    raise ValueError("Invalid file path detected")

                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        return f"Template file is empty: {self.file_path}"
                    return content
            except FileNotFoundError:
                return f"Template file not found: {self.file_path}"
            except PermissionError:
                return f"Permission denied reading template file: {self.file_path}"
            except UnicodeDecodeError:
                return f"Template file encoding error: {self.file_path}"
            except ValueError as e:
                return f"Template file error: {str(e)}"
            except Exception as e:
                return f"Unexpected error reading template file: {str(e)}"
        else:
            return self.content or ""
    
    def save_content(self, content):
        """Save template content, either to database or file"""
        if self.template_type == TemplateType.FILE.value and self.file_path:
            try:
                # Validate file path to prevent directory traversal
                if '..' in self.file_path or self.file_path.startswith('/'):
                    raise ValueError("Invalid file path detected")

                # Validate content
                if not isinstance(content, str):
                    raise ValueError("Content must be a string")

                # Create directory if it doesn't exist
                directory = os.path.dirname(self.file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                # Write content to file
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except (OSError, ValueError, PermissionError) as e:
                # Log the error for debugging
                import logging
                logging.getLogger(__name__).error(f"Error saving template file {self.file_path}: {str(e)}")
                return False
            except Exception as e:
                # Log unexpected errors
                import logging
                logging.getLogger(__name__).error(f"Unexpected error saving template file {self.file_path}: {str(e)}")
                return False
        else:
            try:
                if not isinstance(content, str):
                    raise ValueError("Content must be a string")
                self.content = content
                return True
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving template content: {str(e)}")
                return False

class JobApplication(db.Model):
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



class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # CV, Cover Letter
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class JobLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    note = db.Column(db.Text, nullable=False)
    status_change_from = db.Column(db.String(50))  # Previous status if this log represents a status change
    status_change_to = db.Column(db.String(50))    # New status if this log represents a status change

    def __repr__(self):
        return f'<JobLog {self.id}: {self.note[:50]}...>'










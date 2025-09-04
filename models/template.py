"""
Template model for managing cover letter and CV templates
"""
import os
from datetime import datetime, timezone
from .base import db
from .enums import TemplateType


class MasterTemplate(db.Model):
    """Model for managing master templates (cover letters, CVs, etc.)"""
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

    def __repr__(self)  -> str:
        return f'<MasterTemplate {self.name}>'

"""
User data model
"""
from .base import db


class UserData(db.Model):
    """Model for storing user profile information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))

    def __repr__(self):
        return f'<UserData {self.name} ({self.email})>'

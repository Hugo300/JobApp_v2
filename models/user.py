"""
User data model
"""
from .base import db
from sqlalchemy.ext.associationproxy import association_proxy


class UserData(db.Model):
    """Model for storing user profile information"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))

    user_skills = db.relationship('UserSkill', backref='user_data', lazy=True, cascade='all, delete-orphan')

    # Association proxy for direct access to skills
    skills = association_proxy('user_skills', 'skills')

    def __repr__(self):
        return f'<UserData {self.name} ({self.email})>'


class UserSkill(db.Model):
    """Model for job application skills"""
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user_data.id'), nullable=False)  # Corrected foreign key
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)

    def __repr__(self):
        return f"<UserSkill(user_id={self.user_id}, skill_id={self.skill_id})>"
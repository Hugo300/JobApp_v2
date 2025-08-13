from sqlalchemy.orm import relationship
from .base import db

class Skill(db.Model):
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('skill_categories.id'), nullable=True)
    is_blacklisted = db.Column(db.Boolean, default=False)

    # Add relationships
    skill_jobs = relationship('JobSkill', backref='skills', lazy=True, cascade='all, delete-orphan')
    skill_category = relationship('SkillCategory', backref='skills', lazy=True)

    def __repr__(self):
        return f"<Skill(name={self.name}, category_id={self.category_id})>"


class SkillCategory(db.Model):
    __tablename__ = 'skill_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.String(500), nullable=True)

    def __init__(self, name, description=None):
        self.name = name
        self.description = description

    def __repr__(self):
        return f"<SkillCategory(name={self.name})>"
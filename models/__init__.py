"""
Models package for JobApp_v2

This package contains all database models organized into separate modules:
- base: Database setup and common imports
- enums: Application enums (ApplicationStatus, TemplateType, JobMode)
- user: User data model
- template: Template management model
- job: Job application, document, and log models
"""

# Import base database setup
from .base import db

# Import enums
from .enums import ApplicationStatus, TemplateType, JobMode

# Import models
from .user import UserData, UserSkill
from .template import MasterTemplate
from .job import JobApplication, Document, JobLog, JobSkill
from .skill import Skill, SkillCategory, SkillVariant

# Make everything available at package level
__all__ = [
    'db',
    'ApplicationStatus',
    'TemplateType',
    'JobMode',
    'UserData',
    'UserSkill',
    'MasterTemplate',
    'JobApplication',
    'Document',
    'JobLog',
    'JobSkill',
    'Skill',
    'SkillCategory',
    'SkillVariant',
]










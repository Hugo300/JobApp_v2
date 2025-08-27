"""
Enums used across the application models
"""
from enum import Enum


class ApplicationStatus(Enum):
    COLLECTED = "Collected"
    APPLIED = "Applied"
    PROCESS = "Process"
    WAITING_DECISION = "Waiting Decision"
    OFFER = "Offer"
    ACCEPTED = "Completed"
    REJECTED = "Rejected"


class TemplateType(Enum):
    DATABASE = "database"
    FILE = "file"


class JobMode(Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"

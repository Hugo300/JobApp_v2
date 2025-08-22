# Routes package

# Core routes
from .main import main_bp
from .templates import templates_bp
from .jobs import jobs_bp
from .skills import skills_bp
from .skills_new import skill_new_bp
from .user import user_bp

__all__ = [
    'main_bp',
    'jobs_bp',
    'templates_bp',
    'skills_bp',
    'user_bp',
    'skill_new_bp',
]

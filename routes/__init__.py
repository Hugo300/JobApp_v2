# Routes package

# Core routes
from .main import main_bp
from .templates import templates_bp
from .jobs import jobs_bp

from .skills import skill_bp
from .categories import skill_category_bp

from .user import user_bp

from .analytics import analytics_bp

__all__ = [
    'main_bp',
    'jobs_bp',
    'templates_bp',
    'user_bp',
    'skill_bp',
    'skill_category_bp',
    'analytics_bp',
]

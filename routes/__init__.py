# Routes package with conditional imports

# Core routes that should always work
from .main import main_bp
from .templates import templates_bp

# Routes that might have dependencies
try:
    from .jobs import jobs_bp
    JOBS_ROUTES_AVAILABLE = True
except ImportError:
    # Create a minimal jobs blueprint
    from flask import Blueprint
    jobs_bp = Blueprint('jobs', __name__)
    JOBS_ROUTES_AVAILABLE = False

try:
    from .skills import skills_bp
    SKILLS_ROUTES_AVAILABLE = True
except ImportError:
    from flask import Blueprint
    skills_bp = Blueprint('skills', __name__)
    SKILLS_ROUTES_AVAILABLE = False

__all__ = [
    'main_bp',
    'jobs_bp',
    'templates_bp',
    'skills_bp',
]

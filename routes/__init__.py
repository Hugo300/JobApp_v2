# Routes package

# Core routes
from .main import main_bp
from .templates import templates_bp
from .jobs import jobs_bp

__all__ = [
    'main_bp',
    'jobs_bp',
    'templates_bp',
]

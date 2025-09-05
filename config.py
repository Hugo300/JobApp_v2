import os
import secrets
from datetime import timedelta
import logging
from logging.handlers import RotatingFileHandler

class Config:
    """Base configuration class"""
    # Generate a secure secret key if not provided
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///job_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'documents'

    # Flask-WTF CSRF Protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600  # 1 hour

    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Application settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload

    # LaTeX compilation timeout
    LATEX_TIMEOUT = 60  # seconds

    # Web scraping settings
    SCRAPING_TIMEOUT = 10  # seconds
    SCRAPING_USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'

    # Security settings
    SEND_FILE_MAX_AGE_DEFAULT = timedelta(hours=1)

    ## Logging configuration (centralized)
    LOG_FOLDER = os.path.join(os.getcwd(), 'logs')
    LOG_LEVEL = logging.INFO
    LOG_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_BACKUP_COUNT = 10

    @staticmethod
    def validate_config():
        """Validate required configuration values"""
        required_vars = []
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        return True

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_ECHO = False  # Set to True to see SQL queries

    # Development-specific logging
    LOG_LEVEL = logging.DEBUG

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # Require SECRET_KEY in production
    SECRET_KEY = os.environ.get('SECRET_KEY')

    # Security settings for production
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Strict'

    # Use PostgreSQL in production if available
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              os.environ.get('POSTGRES_URL') or \
                              'sqlite:///job_app.db'
    
    # Production-specific logging
    LOG_LEVEL = logging.INFO
    LOG_MAX_BYTES = 50 * 1024 * 1024  # 50MB for production
    LOG_BACKUP_COUNT = 20

    @staticmethod
    def validate_config():
        """Validate required configuration values for production"""
        required_vars = ['SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.environ.get(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables for production: {', '.join(missing_vars)}")
        return True

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False  # Disable CSRF for testing

    # Testing-specific logging
    LOG_LEVEL = logging.WARNING  # Reduce log noise in tests

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

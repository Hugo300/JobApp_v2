import os
import logging
import time
from logging.handlers import RotatingFileHandler
from flask import Flask, request, g, render_template
from flask_wtf.csrf import CSRFProtect
from flask_bootstrap import Bootstrap5
from config import config
from models import db

from logging_manager import logging_manager

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    bootstrap = Bootstrap5(app)

    # Initialize centralized logging
    logging_manager.init_app(app)

    # Validate configuration
    try:
        config[config_name].validate_config()
    except (ValueError, AttributeError) as e:
        app.logger.warning(f"Configuration validation warning: {e}")

    csrf = CSRFProtect(app)

    db.init_app(app)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        """Add security headers to all responses"""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # Add CSP header for better XSS protection
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "font-src 'self' https://cdnjs.cloudflare.com; "
            "img-src 'self' data:; "
            "connect-src 'self';"
        )
        response.headers['Content-Security-Policy'] = csp

        return response

        # Add request logging for security monitoring
    @app.before_request
    def log_request_info():
        """Log request information for security monitoring"""
        logging_manager.log_request_info(request)
        # Store request start time for performance monitoring
        g.start_time = time.time()

    # Register blueprints
    from routes import main_bp, jobs_bp, templates_bp, skill_bp, user_bp, skill_category_bp, analytics_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix='/job')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(skill_bp, url_prefix='/admin/skills')
    app.register_blueprint(skill_category_bp, url_prefix='/admin/categories')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(analytics_bp, url_prefix='/analytics')

    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        logging_manager.log_security_event('404_ERROR', f'Page not found: {request.url}', request)
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logging_manager.log_error(error, f'Internal server error at {request.url}')
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def file_too_large(error):
        """Handle file upload size errors"""
        logging_manager.log_security_event('FILE_TOO_LARGE', f'Large file upload attempt: {request.url}', request)
        return render_template('errors/413.html'), 413
    
    with app.app_context():
        db.create_all()

    return app

if __name__ == '__main__':
    # Set development environment if not specified
    os.environ.setdefault('FLASK_ENV', 'development')
    app = create_app()

    try:
        app.run(
            host=os.environ.get('HOST', '127.0.0.1'),
            port=int(os.environ.get('PORT', 7000)),
            debug=app.config.get('DEBUG', False)
        )
    finally:
        # Clean up logging handlers on shutdown
        logging_manager.cleanup()

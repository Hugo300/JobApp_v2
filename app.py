import os
import logging
import time
from logging.handlers import RotatingFileHandler
from flask import Flask, request, g, render_template
from flask_wtf.csrf import CSRFProtect

from config import config
from models import db

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

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
        if not app.debug:
            app.logger.info(f"Request: {request.method} {request.url} from {request.remote_addr}")
            # Store request start time for performance monitoring
            g.start_time = time.time()

    # Register blueprints
    from routes.main import main_bp
    from routes.jobs import jobs_bp
    from routes.templates import templates_bp
    from routes.skills import skills_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix='/job')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    app.register_blueprint(skills_bp, url_prefix='/skills')

    # Add error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors"""
        app.logger.warning(f"404 error: {request.url}")
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        app.logger.error(f"500 error: {error}")
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(413)
    def file_too_large(error):
        """Handle file upload size errors"""
        app.logger.warning(f"File too large: {request.url}")
        return render_template('errors/413.html'), 413
    
    # Configure logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/job_app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Job Application Manager startup')

    with app.app_context():
        db.create_all()



    return app

if __name__ == '__main__':
    # Set development environment if not specified
    os.environ.setdefault('FLASK_ENV', 'development')
    app = create_app()
    app.run(
        host=os.environ.get('HOST', '127.0.0.1'),
        port=int(os.environ.get('PORT', 7000)),
        debug=app.config.get('DEBUG', False)
    )

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect

from config import config, Config
from models import db, UserData, MasterTemplate, JobApplication, Document, JobLog, ApplicationStatus, TemplateType, JobMode

def create_app(config_name=None):
    """Application factory pattern"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')

    app = Flask(__name__)
    app.config.from_object(config[config_name])

    bootstrap = Bootstrap(app)
    csrf = CSRFProtect(app)

    db.init_app(app)

    from routes.main import main_bp
    from routes.jobs import jobs_bp
    from routes.templates import templates_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix='/job')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    
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

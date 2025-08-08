from flask import Flask
from config import Config
from models import db

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    # Import models after db is initialized
    from models import UserData, MasterTemplate, JobApplication, Document
    
    from routes.main import main_bp
    from routes.jobs import jobs_bp
    from routes.templates import templates_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(jobs_bp, url_prefix='/job')
    app.register_blueprint(templates_bp, url_prefix='/templates')
    
    with app.app_context():
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='127.0.0.1',
        port=7000,
        debug=True
    )

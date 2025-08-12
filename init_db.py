"""
Initialize the database with all tables
"""
from app import create_app
from models import db

def init_database():
    """Initialize the database with all tables"""
    app = create_app()
    
    with app.app_context():
        print("Creating all database tables...")
        db.create_all()
        print("✓ Database tables created successfully!")
        
        # List all tables
        inspector = db.inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"Tables created: {', '.join(tables)}")

if __name__ == "__main__":
    init_database()

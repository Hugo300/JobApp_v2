"""
Base database setup and common imports for models
"""
from flask_sqlalchemy import SQLAlchemy

# We'll get db from the app context instead of importing directly
db = SQLAlchemy()

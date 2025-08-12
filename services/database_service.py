"""
Database service with proper error handling and transaction management
"""
import logging
from contextlib import contextmanager
from typing import Optional, Any, Callable
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from flask import current_app
from models import db


class DatabaseService:
    """Service for handling database operations with proper error handling"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions with automatic rollback on error
        
        Usage:
            with db_service.transaction():
                # database operations
                db.session.add(obj)
                # transaction is automatically committed
        """
        try:
            yield db.session
            db.session.commit()
            self.logger.debug("Database transaction committed successfully")
        except IntegrityError as e:
            db.session.rollback()
            self.logger.error(f"Database integrity error: {str(e)}")
            raise DatabaseIntegrityError(f"Data integrity violation: {str(e)}")
        except OperationalError as e:
            db.session.rollback()
            self.logger.error(f"Database operational error: {str(e)}")
            raise DatabaseOperationalError(f"Database operation failed: {str(e)}")
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error: {str(e)}")
            raise DatabaseError(f"Database error: {str(e)}")
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Unexpected error in database transaction: {str(e)}")
            raise DatabaseError(f"Unexpected database error: {str(e)}")
    
    def safe_execute(self, operation: Callable, *args, **kwargs) -> tuple[bool, Optional[Any], Optional[str]]:
        """
        Safely execute a database operation with error handling
        
        Args:
            operation: Function to execute
            *args: Arguments for the operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            tuple: (success: bool, result: Any, error_message: str)
        """
        try:
            with self.transaction():
                result = operation(*args, **kwargs)
                return True, result, None
        except DatabaseError as e:
            return False, None, str(e)
        except Exception as e:
            self.logger.error(f"Unexpected error in safe_execute: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def safe_query(self, query_func: Callable, *args, **kwargs) -> tuple[bool, Optional[Any], Optional[str]]:
        """
        Safely execute a database query with error handling
        
        Args:
            query_func: Query function to execute
            *args: Arguments for the query
            **kwargs: Keyword arguments for the query
            
        Returns:
            tuple: (success: bool, result: Any, error_message: str)
        """
        try:
            result = query_func(*args, **kwargs)
            return True, result, None
        except SQLAlchemyError as e:
            self.logger.error(f"Database query error: {str(e)}")
            return False, None, f"Query failed: {str(e)}"
        except Exception as e:
            self.logger.error(f"Unexpected error in safe_query: {str(e)}")
            return False, None, f"Unexpected error: {str(e)}"
    
    def create_object(self, model_class, **kwargs) -> tuple[bool, Optional[Any], Optional[str]]:
        """
        Safely create a new database object
        
        Args:
            model_class: SQLAlchemy model class
            **kwargs: Object attributes
            
        Returns:
            tuple: (success: bool, object: Any, error_message: str)
        """
        def _create():
            obj = model_class(**kwargs)
            db.session.add(obj)
            db.session.flush()  # Get the ID without committing
            return obj
        
        return self.safe_execute(_create)
    
    def update_object(self, obj, **kwargs) -> tuple[bool, Optional[Any], Optional[str]]:
        """
        Safely update a database object
        
        Args:
            obj: Object to update
            **kwargs: Attributes to update
            
        Returns:
            tuple: (success: bool, object: Any, error_message: str)
        """
        def _update():
            for key, value in kwargs.items():
                if hasattr(obj, key):
                    setattr(obj, key, value)
            return obj
        
        return self.safe_execute(_update)
    
    def delete_object(self, obj) -> tuple[bool, None, Optional[str]]:
        """
        Safely delete a database object
        
        Args:
            obj: Object to delete
            
        Returns:
            tuple: (success: bool, None, error_message: str)
        """
        def _delete():
            db.session.delete(obj)
            return None
        
        return self.safe_execute(_delete)


# Custom exceptions for better error handling
class DatabaseError(Exception):
    """Base exception for database errors"""
    pass


class DatabaseIntegrityError(DatabaseError):
    """Exception for database integrity violations"""
    pass


class DatabaseOperationalError(DatabaseError):
    """Exception for database operational errors"""
    pass


# Global instance
db_service = DatabaseService()

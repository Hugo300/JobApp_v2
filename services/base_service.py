"""
Base service class with common functionality
Enhanced with skill utilities and common patterns
"""
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from models import db
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone

import logging

# Configure module logger
logger = logging.getLogger(__name__)

class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def safe_execute(self, operation, *args, **kwargs):
        """
        Safely execute a database operation with error handling
        
        Args:
            operation: Function to execute
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            tuple: (success: bool, result: any, error: str)
        """
        try:
            result = operation(*args, **kwargs)
            db.session.commit()
            return True, result, None
        
        except SQLAlchemyError as e:
            db.session.rollback()
            error_msg = f"Database error: {e!s}"
            self.logger.exception(error_msg)
            return False, None, error_msg
        
        except Exception as e:
            db.session.rollback()
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    def get_by_id(self, model_class, id):
        """
        Get a model instance by ID

        Args:
            model_class: The model class
            id: The ID to search for

        Returns:
            Model instance or None
        """
        try:
            return db.session.get(model_class, id)
        except Exception as e:
            self.logger.error(f"Error getting {model_class.__name__} by ID {id}: {str(e)}")
            return None
    
    def get_all(self, model_class, order_by=None):
        """
        Get all instances of a model

        Args:
            model_class: The model class
            order_by: Optional ordering column

        Returns:
            List of model instances
        """
        try:
            query = model_class.query
            if order_by is not None:
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting all {model_class.__name__}: {str(e)}")
            return []
    
    def create(self, model_class, **kwargs):
        """
        Create a new model instance
        
        Args:
            model_class: The model class
            **kwargs: Model attributes
            
        Returns:
            tuple: (success: bool, instance: Model, error: str)
        """
        def _create():
            instance = model_class(**kwargs)
            db.session.add(instance)
            return instance
        
        return self.safe_execute(_create)
    
    def update(self, instance, **kwargs):
        """
        Update a model instance
        
        Args:
            instance: The model instance to update
            **kwargs: Attributes to update
            
        Returns:
            tuple: (success: bool, instance: Model, error: str)
        """
        def _update():
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            return instance
        
        return self.safe_execute(_update)
    
    def delete(self, instance):
        """
        Delete a model instance
        
        Args:
            instance: The model instance to delete
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        def _delete():
            db.session.delete(instance)
            return True
        
        return self.safe_execute(_delete)
    
    def filter_by(self, model_class, order_by=None, **filters):
        """
        Filter model instances

        Args:
            model_class: The model class
            order_by: Optional ordering column
            **filters: Filter criteria

        Returns:
            List of model instances
        """
        try:
            query = model_class.query.filter_by(**filters)
            if order_by is not None:
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error filtering {model_class.__name__}: {str(e)}")
            return []
    
    def paginate(self, model_class, page=1, per_page=20, order_by=None, **filters):
        """
        Paginate model instances
        
        Args:
            model_class: The model class
            page: Page number
            per_page: Items per page
            order_by: Optional ordering column
            **filters: Filter criteria
            
        Returns:
            Pagination object
        """
        try:
            query = model_class.query
            if filters:
                query = query.filter_by(**filters)
            if order_by is not None:
                query = query.order_by(order_by)
            return query.paginate(page=page, per_page=per_page, error_out=False)
        except Exception as e:
            self.logger.error(f"Error paginating {model_class.__name__}: {str(e)}")
            return None




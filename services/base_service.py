"""
Base service class with common functionality
Enhanced with skill utilities and common patterns
"""
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from models import db
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
from utils.skill_constants import (
    get_skill_category, get_canonical_skill_name,
    is_soft_skill, is_noise_skill
)
import logging


class BaseService:
    """Base service class with common database operations"""
    
    def __init__(self):
        self.logger = current_app.logger if current_app else logging.getLogger(__name__)
    
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
            error_msg = f"Database error: {str(e)}"
            self.logger.error(error_msg)
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


class SkillServiceMixin:
    """Mixin class providing common skill-related functionality"""

    def _normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name using canonical mapping"""
        if not skill or not isinstance(skill, str):
            return ""

        # Basic cleaning
        normalized = skill.strip().lower()

        # Get canonical name
        canonical = get_canonical_skill_name(normalized)

        # Return with proper capitalization
        return canonical.title() if canonical else skill.strip()

    def _categorize_skill(self, skill: str) -> str:
        """Get category for a skill"""
        return get_skill_category(skill)

    def _is_soft_skill(self, skill: str) -> bool:
        """Check if skill is a soft skill"""
        return is_soft_skill(skill)

    def _is_valid_skill(self, skill: str) -> bool:
        """Validate if a skill is legitimate (not noise)"""
        if not skill or not isinstance(skill, str):
            return False

        skill_clean = skill.strip()

        # Length checks
        if len(skill_clean) < 2 or len(skill_clean) > 100:
            return False

        # Check against noise patterns
        if is_noise_skill(skill_clean):
            return False

        return True

    def _deduplicate_skills(self, skills: List[str]) -> List[str]:
        """Remove duplicate skills while preserving order"""
        if not skills:
            return []

        seen = set()
        unique_skills = []

        for skill in skills:
            normalized = self._normalize_skill_name(skill)
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                unique_skills.append(normalized)

        return unique_skills

    def _filter_skills(self, skills: List[str], include_soft_skills: bool = True,
                      min_length: int = 2, max_length: int = 50) -> List[str]:
        """Filter skills based on various criteria"""
        if not skills:
            return []

        filtered = []
        for skill in skills:
            # Validate skill
            if not self._is_valid_skill(skill):
                continue

            # Length check
            if len(skill) < min_length or len(skill) > max_length:
                continue

            # Soft skills filter
            if not include_soft_skills and self._is_soft_skill(skill):
                continue

            filtered.append(skill)

        return filtered

    def _calculate_skill_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills"""
        if not skill1 or not skill2:
            return 0.0

        skill1_lower = skill1.lower().strip()
        skill2_lower = skill2.lower().strip()

        # Exact match
        if skill1_lower == skill2_lower:
            return 1.0

        # Check if one contains the other
        if skill1_lower in skill2_lower or skill2_lower in skill1_lower:
            return 0.8

        # Check canonical names
        canonical1 = get_canonical_skill_name(skill1_lower)
        canonical2 = get_canonical_skill_name(skill2_lower)

        if canonical1 == canonical2:
            return 0.9

        # Word-based similarity
        words1 = set(skill1_lower.split())
        words2 = set(skill2_lower.split())

        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            return len(intersection) / len(union) if union else 0.0

        return 0.0

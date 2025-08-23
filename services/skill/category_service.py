from typing import Optional, Tuple
from sqlalchemy.exc import SQLAlchemyError

from models import SkillCategory, Skill, db
from base_service import BaseService

from utils.forms import sanitize_input

class CategoryService(BaseService):

    def get_category_by_id(self, category_id):
        return self.get_by_id(SkillCategory, category_id)
    
    def get_category_by_name(self, name):
        return self.filter_by(
            SkillCategory,
            order=None,
            name=name
        )
    
    def get_all_categories(self, order_by=None, include_relationships=False):
        """
        Get all categories with optimized queries

        Args:
            order_by: Order by clause
            include_relationships: Whether to eagerly load relationships

        Returns:
            List[SkillCategory]: List of categories
        """
        try:
            query = SkillCategory.query

            # Eagerly load relationships to prevent N+1 queries
            if include_relationships:
                from sqlalchemy.orm import joinedload
                query = query.options(
                    joinedload(Skill.category),
                )

            if order_by is None:
                query = query.order_by(SkillCategory.name.desc())
            else:
                query = query.order_by(order_by)

            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting all skills: {str(e)}")
            return []

    def create_category(self, name: str, description: str) -> Tuple[bool, Optional[SkillCategory], Optional[str]]:
        """Create a new category"""
        # Validate and sanitize inputs
        if not name or not name.strip():
            return False, None, "Name is required"
        
        name = sanitize_input(name)
        description = sanitize_input(description)
        
        # Check if category already exists
        existing_category = self.get_category_by_name(name=name)
        if existing_category:
            return False, None, f"Category '{name}' already exists"
        
        # Create new category
        return self.create(
            SkillCategory,
            **{'name': name, 'description': description}
        )
    
    def update_category(self, category_id: int, **kwargs) -> Tuple[bool, Optional[SkillCategory], Optional[str]]:
        """Update a category"""
        category = SkillCategory.query.get(category_id)
        if not category:
            return False, None, "Category not found"
        
        # Update attributes
        return self.update(
            SkillCategory,
            **kwargs
        )
    
    def delete_category(self, category_id: int) -> Tuple[bool, Optional[bool], Optional[str]]:
        """Delete a category"""
        category = self.get_category_by_id(category_id)
        if not category:
            return False, False, "Category not found"
        
        return self.delete(category)

    
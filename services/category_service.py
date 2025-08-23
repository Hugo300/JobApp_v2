from models import SkillCategory, Skill
from utils.forms import sanitize_input
from .base_service import BaseService


class CategoryService(BaseService):
    def __init__(self):
        super().__init__()

    def get_category_by_id(self, category_id):
        return self.get_by_id(SkillCategory, category_id)
    
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
        
    def create_category(self, name, description=None):
        """
        Create a new category

        Args:
            name: category name
            description: category description

        Returns:
            tuple: (success: bool, category: SkillCategory, error: str)
        """
        # Validate and sanitize inputs
        try:
            if not name or not name.strip():
                return False, None, "Name is required"

            # Sanitize all string inputs
            name = sanitize_input(name)
            description = sanitize_input(description)

        except Exception as e:
            self.logger.error(f"Error validating category data: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

        data = {
            'name': name,
            'description': description,
        }

        # Create the category
        success, obj, error = self.create(SkillCategory, **data)

        return success, obj, error
    
    def update_category(self, category_id, **kwargs):
        """
        Update a category

        Args:
            category_id: category ID
            **kwargs: Fields to update

        Returns:
            tuple: (success: bool, category: SkillCategory, error: str)
        """
        category = self.get_skill_by_id(category_id)
        if not category:
            return False, None, "SkillCategory not found"

        # Update the skill
        success, updated_skill, error = self.update(category, **kwargs)

        return success, updated_skill, error
    
    def delete_category(self, category_id):
        """
        Delete a category
        
        Args:
            category_id: category ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        category = self.get_category_by_id(category_id)
        if not category:
            return False, None, "category not found"
        
        return self.delete(category)


from typing import List, Tuple, Optional, Dict, Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from flask import current_app
import logging

from models import SkillCategory, Skill, db
from ..base_service import BaseService

# Configure module logger
logger = logging.getLogger(__name__)

class CategoryService(BaseService):
    """Service class for managing skill categories"""
    
    def __init__(self):
        super().__init__()
        self._cache_valid = False
        self._cache = {}
        self.logger.info("CategoryService initialized")
    
    def get_all_categories(self, include_counts: bool = False) -> List[SkillCategory]:
        """Get all skill categories, optionally with skill counts"""
        try:
            self.logger.debug(f"Fetching all categories")
            categories = SkillCategory.query.all()

            if categories:
                self.logger.debug(f"Categories found")
            else:
                self.logger.warning(f"No categories were found")
            
            if include_counts:
                for category in categories:
                    category.skill_count = self._get_skills_count_for_category(category.id)
                    category.active_skill_count = self._get_active_skills_count_for_category(category.id)
            
            return categories
            
        except Exception as e:
            self.logger.error(f"Error fetching categories: {str(e)}", exc_info=True)
            return []
    
    def get_category_by_id(self, category_id: int, include_skills: bool = False) -> Optional[SkillCategory]:
        """Get a category by ID, optionally with associated skills"""
        try:
            self.logger.debug(f"Fetching category by ID: {category_id}")
            if include_skills:
                category = SkillCategory.query.options(
                    joinedload(SkillCategory.skills)
                ).get(category_id)
            else:
                category = SkillCategory.query.get(category_id)

            if category:
                self.logger.debug(f"Category found: {category.name}")
            else:
                self.logger.warning(f"Category not found with ID: {category_id}")
            
            return category
            
        except Exception as e:
            self.logger.error(f"Error fetching category by ID {category_id}: {str(e)}", exc_info=True)
            return None
    
    def get_category_by_name(self, name: str) -> Optional[SkillCategory]:
        """Get a category by name"""
        self.logger.debug(f"Fetching category by Name: {name}")
        try:
            category = SkillCategory.query.filter_by(name=name).first()

            if category:
                self.logger.debug(f"Category found: {category.name}")
            else:
                self.logger.warning(f"Category not found with Name: {name}")
            
            return category
        
        except Exception as e:
            self.logger.error(f"Error fetching category by Name {name}: {str(e)}", exc_info=True)
            return None
    
    def create_category(self, name: str, description: str = None) -> Tuple[bool, Optional[SkillCategory], str|None]:
        """
        Create a new skill category
        Returns: (success, category, error_message)
        """
        self.logger.info(f"Creating new category: {name} - {description}")

        try:
            # Validate input
            if not name or not name.strip():
                self.logger.warning("Category creation failed: Category name is required")
                return False, None, "Category name is required"
            
            name = name.strip()
            description = description.strip() if description else None
            
            # Check if category already exists
            existing = self.get_category_by_name(name)
            if existing:
                self.logger.warning("Category already exists with that name")
                return False, None, "A category with this name already exists"
    
        except Exception as e:
            self.logger.error(f"Error validating category data for {name}: {str(e)}", exc_info=True)
            return False, None, f"Validation error: {str(e)}"
        
        category_data = {
            'name': name,
            'description': description
        }

        # Create the Category
        success, category, error = self.create(SkillCategory, **category_data)

        if success:
            self.logger.info(f"Category created successfully: ID={category.id}, {name} - {description}")
        else:
            self.logger.error(f"Failed to create Category with name {name}: {error}")

        return success, category, error
    
    def update_category(self, category_id: int, **kwargs) -> Tuple[bool, Optional[SkillCategory], str|None]:
        """
        Update an existing skill category
        Returns: (success, category, error_message)
        """
        self.logger.info(f"Updating category ID: {category_id}")
        self.logger.debug(f"Update fields: {list(kwargs.keys())}")

        category = self.get_category_by_id(category_id)
        if not category:
            self.logger.warning(f"Update failed: Category not found with ID: {category_id}")
            return False, None, "Category not found"
            
        # Log what's being updated
        updated_fields = []
        for key, value in kwargs.items():
            if hasattr(category, key) and getattr(category, key) != value:
                old_value = getattr(category, key)
                updated_fields.append(f"{key}: '{old_value}' -> '{value}'")
            
        # Update the category
        success, updated_category, error = self.update(category, **kwargs)
            
        if success:
            self.logger.info(f"Category {category_id} updated successfully")
            if updated_fields:
                self.logger.debug(f"Changed fields: {', '.join(updated_fields)}")
        else:
            self.logger.error(f"Failed to update category {category_id}: {error}")

        return success, updated_category, error
    
    def delete_category(self, category_id: int, skill_action: str = 'keep') -> Tuple[bool, Dict[str, Any]|None, str|None]:
        """
        Delete a skill category
        skill_action: 'keep' (move to uncategorized), 'delete' (delete skills), 'cancel' (don't delete if has skills)
        Returns: (success, result_info, error_message)
        """
        self.logger.info(f"Deleting category ID: {category_id}")
  
        category = self.get_category_by_id(category_id)
        if not category:
            self.logger.warning(f"Delete failed: Category not found with ID: {category_id}")
            return False, None, "Category not found"
        
        # Log category details before deletion
        self.logger.info(f"Deleting category: {category.name} - {category.description}")

        skills_in_category = Skill.query.filter_by(category_id=category_id).all()
        skills_count = len(skills_in_category)

        if skills_count > 0:
            if skill_action == 'cancel':
                self.logger.warning(f"Delete failed: Category has associated skills")
                return False, None, "Category deletion cancelled - category has associated skills"
            elif skill_action == 'keep':
                # Move skills to uncategorized
                for skill in skills_in_category:
                    skill.category_id = None
                self.logger.info(f"Skills moved to uncategorized: count {skills_count}")
            elif skill_action == 'delete':
                # Delete all skills in this category
                for skill in skills_in_category:
                    if skill.skill_jobs:
                        self.logger.warning(f"Delete failed: Cannot delete skill referenced by jobs")
                        return False, None, f"Cannot delete skills that are referenced by jobs"
                
                # Safe to delete all skills
                for skill in skills_in_category:
                    self.delete(skill)

                self.logger.info(f"Skills have been deleted")

        success, _result, error = self.delete(category)

        if success:
            self.logger.info(f"Category {category_id} deleted successfully")
            result_info = {  
                "category_name": category.name,  
                "message": (  
                    f"Moved {skills_count} skills to uncategorized"  
                    if skills_count > 0 and skill_action == "keep" else None  
                ),  
            }  
            return True, result_info, None  
        else:
            self.logger.error(f"Failed to delete category {category_id}: {error}")
            return False, None, error
    
    def get_category_skills(self, category_id: int) -> Tuple[List[Skill], List[Skill], List[Skill]]:
        """
        Get skills for a category, separated by status
        Returns: (all_skills, active_skills, blacklisted_skills)
        """
        self.logger.info(f"Fetching skills for category ID: {category_id}")
        try:
            all_skills = Skill.query.filter_by(category_id=category_id).all()
            active_skills = [s for s in all_skills if not s.is_blacklisted]
            blacklisted_skills = [s for s in all_skills if s.is_blacklisted]
            
            self.logger.info(f"Fetched {len(all_skills)} skills for category ID: {category_id}")

            return all_skills, active_skills, blacklisted_skills
            
        except Exception as e:
            self.logger.error(f"Error getting skills for category {category_id}: {str(e)}", exc_info=True)
            return [], [], []
    
    def get_stats(self) -> Dict[str, int]:
        """Get category and skill statistics"""
        try:
            self.logger.debug("Calculating category statistics")

            total_categories = SkillCategory.query.count()
            total_skills = Skill.query.count()
            uncategorized_skills = Skill.query.filter_by(category_id=None).count()
            categorized_skills = total_skills - uncategorized_skills

            self.logger.info(f"Statistics calculated for {total_categories} categories: "
                           f"{total_skills} skills of which {categorized_skills} are categorized")
            
            return {
                'total_categories': total_categories,
                'total_skills': total_skills,
                'categorized_skills': categorized_skills,
                'uncategorized_skills': uncategorized_skills
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating category statistics: {str(e)}", exc_info=True)
            return {
                'total_categories': 0,
                'total_skills': 0,
                'categorized_skills': 0,
                'uncategorized_skills': 0
            }
    
    def move_skills_to_category(self, skill_ids: List[int], target_category_id: Optional[int]) -> Tuple[bool, int, str]:
        """
        Move multiple skills to a category (or uncategorized if target_category_id is None)
        Returns: (success, count_moved, error_message)
        """
        try:
            self.logger.debug(f"Assigning category {target_category_id} to {len(skill_ids)} skills")

            if target_category_id is not None:
                # Verify target category exists
                target_category = self.get_category_by_id(target_category_id)
                if not target_category:
                    self.logger.warning(f"Target category {target_category_id} not found")
                    return False, 0, "Target category not found"
            
            # Get skills to move
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            if not skills:
                self.logger.warning(f"No skills found to move")
                return False, 0, "No valid skills found to move"
            
            # Move skills
            num_skills = 0
            for skill in skills:
                num_skills += 1
                self.update(skill, category_id=target_category_id)
                       
            self._invalidate_cache()

            self.logger.info(f"Moved {num_skills} skills to category ID {target_category_id}")
            
            return True, len(skills), ""
            
        except Exception as e:
            self.logger.error(f"Error moving skills to category ID {target_category_id}: {str(e)}", exc_info=True)
            return False, 0, str(e)
    
    def _get_skills_count_for_category(self, category_id: int) -> int:
        """Get total number of skills in a category"""
        try:
            self.logger.debug(f"Get number skills for category ID {category_id}")
            return Skill.query.filter_by(category_id=category_id).count()
        except Exception as e:
            self.logger.error(f"Error counting skills for category {category_id}: {str(e)}", exc_info=True)
            return 0
    
    def _get_active_skills_count_for_category(self, category_id: int) -> int:
        """Get number of active (non-blacklisted) skills in a category"""
        try:
            self.logger.debug(f"Get number of active skills for category ID {category_id}")
            return Skill.query.filter_by(category_id=category_id, is_blacklisted=False).count()
        except Exception as e:
            self.logger.error(f"Error counting skills for category {category_id}: {str(e)}", exc_info=True)
            return 0
    
    def _invalidate_cache(self):
        """Invalidate any cached data"""
        self._cache.clear()
        self._cache_valid = False

import threading

# Singleton instance
_category_service_instance = None
_lock = threading.Lock()

def get_category_service() -> CategoryService:
    """Get the singleton CategoryService instance"""
    global _category_service_instance
    if _category_service_instance is None:
        with _lock:
            if _category_service_instance is None:
                _category_service_instance = CategoryService()
    return _category_service_instance
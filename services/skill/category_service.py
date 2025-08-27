from typing import List, Tuple, Optional, Dict, Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload

from flask import current_app

from models import SkillCategory, Skill, db


class CategoryService:
    """Service class for managing skill categories"""
    
    def __init__(self):
        self._cache = {}
        self._cache_valid = False
    
    def get_all_categories(self, include_counts: bool = False) -> List[SkillCategory]:
        """Get all skill categories, optionally with skill counts"""
        try:
            categories = SkillCategory.query.all()
            
            if include_counts:
                for category in categories:
                    category.skill_count = self._get_skills_count_for_category(category.id)
                    category.active_skill_count = self._get_active_skills_count_for_category(category.id)
            
            return categories
            
        except Exception as e:
            current_app.logger.error(f"Error getting categories: {str(e)}")
            return []
    
    def get_category_by_id(self, category_id: int, include_skills: bool = False) -> Optional[SkillCategory]:
        """Get a category by ID, optionally with associated skills"""
        try:
            if include_skills:
                category = SkillCategory.query.options(
                    joinedload(SkillCategory.skills)
                ).get(category_id)
            else:
                category = SkillCategory.query.get(category_id)
            
            return category
            
        except Exception as e:
            print(f"Error getting category {category_id}: {str(e)}")
            return None
    
    def get_category_by_name(self, name: str) -> Optional[SkillCategory]:
        """Get a category by name"""
        try:
            return SkillCategory.query.filter_by(name=name).first()
        except Exception as e:
            print(f"Error getting category by name {name}: {str(e)}")
            return None
    
    def create_category(self, name: str, description: str = None) -> Tuple[bool, Optional[SkillCategory], str]:
        """
        Create a new skill category
        Returns: (success, category, error_message)
        """
        try:
            # Validate input
            if not name or not name.strip():
                return False, None, "Category name is required"
            
            name = name.strip()
            description = description.strip() if description else None
            
            # Check if category already exists
            existing = self.get_category_by_name(name)
            if existing:
                return False, None, "A category with this name already exists"
            
            # Create new category
            category = SkillCategory(name=name, description=description)
            db.session.add(category)
            db.session.commit()
            
            self._invalidate_cache()
            return True, category, ""
            
        except IntegrityError:
            db.session.rollback()
            return False, None, "A category with this name already exists"
        except Exception as e:
            db.session.rollback()
            return False, None, str(e)
    
    def update_category(self, category_id: int, name: str = None, description: str = None) -> Tuple[bool, Optional[SkillCategory], str]:
        """
        Update an existing skill category
        Returns: (success, category, error_message)
        """
        try:
            category = self.get_category_by_id(category_id)
            if not category:
                return False, None, "Category not found"
            
            # Validate name if provided
            if name is not None:
                name = name.strip()
                if not name:
                    return False, None, "Category name cannot be empty"
                
                # Check for name conflicts (excluding current category)
                existing = SkillCategory.query.filter(
                    SkillCategory.name == name,
                    SkillCategory.id != category_id
                ).first()
                
                if existing:
                    return False, None, "A category with this name already exists"
                
                category.name = name
            
            # Update description if provided
            if description is not None:
                category.description = description.strip() if description.strip() else None
            
            db.session.commit()
            self._invalidate_cache()
            return True, category, ""
            
        except IntegrityError:
            db.session.rollback()
            return False, None, "A category with this name already exists"
        except Exception as e:
            db.session.rollback()
            return False, None, str(e)
    
    def delete_category(self, category_id: int, skill_action: str = 'keep') -> Tuple[bool, Dict[str, Any], str]:
        """
        Delete a skill category
        skill_action: 'keep' (move to uncategorized), 'delete' (delete skills), 'cancel' (don't delete if has skills)
        Returns: (success, result_info, error_message)
        """
        try:
            category = self.get_category_by_id(category_id)
            if not category:
                return False, {}, "Category not found"
            
            category_name = category.name
            skills_in_category = Skill.query.filter_by(category_id=category_id).all()
            skills_count = len(skills_in_category)
            
            result_info = {
                'category_name': category_name,
                'skills_count': skills_count,
                'action_taken': skill_action
            }
            
            if skills_count > 0:
                if skill_action == 'cancel':
                    return False, result_info, "Category deletion cancelled - category has associated skills"
                elif skill_action == 'keep':
                    # Move skills to uncategorized
                    for skill in skills_in_category:
                        skill.category_id = None
                    result_info['message'] = f'{skills_count} skills moved to uncategorized'
                elif skill_action == 'delete':
                    # Delete all skills in this category
                    for skill in skills_in_category:
                        if skill.job_skills:
                            return False, result_info, f"Cannot delete skills that are referenced by jobs"
                        db.session.delete(skill)
                    result_info['message'] = f'{skills_count} skills deleted along with category'
            else:
                result_info['message'] = 'Category deleted (no associated skills)'
            
            # Delete the category
            db.session.delete(category)
            db.session.commit()
            
            self._invalidate_cache()
            return True, result_info, ""
            
        except Exception as e:
            db.session.rollback()
            return False, {}, str(e)
    
    def get_category_skills(self, category_id: int) -> Tuple[List[Skill], List[Skill], List[Skill]]:
        """
        Get skills for a category, separated by status
        Returns: (all_skills, active_skills, blacklisted_skills)
        """
        try:
            all_skills = Skill.query.filter_by(category_id=category_id).all()
            active_skills = [s for s in all_skills if not s.is_blacklisted]
            blacklisted_skills = [s for s in all_skills if s.is_blacklisted]
            
            return all_skills, active_skills, blacklisted_skills
            
        except Exception as e:
            print(f"Error getting skills for category {category_id}: {str(e)}")
            return [], [], []
    
    def get_stats(self) -> Dict[str, int]:
        """Get category and skill statistics"""
        try:
            total_categories = SkillCategory.query.count()
            total_skills = Skill.query.count()
            uncategorized_skills = Skill.query.filter_by(category_id=None).count()
            categorized_skills = total_skills - uncategorized_skills
            
            return {
                'total_categories': total_categories,
                'total_skills': total_skills,
                'categorized_skills': categorized_skills,
                'uncategorized_skills': uncategorized_skills
            }
            
        except Exception as e:
            print(f"Error getting stats: {str(e)}")
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
            if target_category_id is not None:
                # Verify target category exists
                target_category = self.get_category_by_id(target_category_id)
                if not target_category:
                    return False, 0, "Target category not found"
            
            # Get skills to move
            skills = Skill.query.filter(Skill.id.in_(skill_ids)).all()
            if not skills:
                return False, 0, "No valid skills found to move"
            
            # Move skills
            for skill in skills:
                skill.category_id = target_category_id
            
            db.session.commit()
            self._invalidate_cache()
            
            return True, len(skills), ""
            
        except Exception as e:
            db.session.rollback()
            return False, 0, str(e)
    
    def _get_skills_count_for_category(self, category_id: int) -> int:
        """Get total number of skills in a category"""
        try:
            return Skill.query.filter_by(category_id=category_id).count()
        except Exception:
            return 0
    
    def _get_active_skills_count_for_category(self, category_id: int) -> int:
        """Get number of active (non-blacklisted) skills in a category"""
        try:
            return Skill.query.filter_by(category_id=category_id, is_blacklisted=False).count()
        except Exception:
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
from typing import List, Dict
from models import SkillCategory, Skill
from .category_service import CategoryService

from exceptions.skill_exceptions import SkillServiceError

class SkillCategorizer:
    """Handles skill categorization logic"""
    
    def categorize_skills(self, skills: List[Skill]) -> Dict[str, List[Skill]]:
        """Categorize skills by their categories"""
        try:
            categorized_skills = {}
            
            # Categorize skills
            for skill in skills:
                if skill.category_id:
                    category = CategoryService().get_category_by_id(skill.category_id)
                    if category.name not in categorized_skills:
                        categorized_skills[category.name] = []
                    categorized_skills[category.name].append(skill)
                else:
                    # Uncategorized skills
                    if 'Uncategorized' not in categorized_skills:
                        categorized_skills['Uncategorized'] = []
                    categorized_skills['Uncategorized'].append(skill)
            
            return categorized_skills
            
        except Exception as e:
            raise SkillServiceError(f"Failed to categorize skills: {str(e)}")
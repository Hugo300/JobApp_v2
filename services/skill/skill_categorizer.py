from typing import List, Dict
from models import SkillCategory, Skill

from exceptions.skill_exceptions import SkillServiceError

class SkillCategorizer:
    """Handles skill categorization logic"""
    
    def categorize_skills(self, skills: List[Skill]) -> Dict[str, List[Skill]]:
        """Categorize skills by their categories"""
        try:
            categorized_skills = {}
            
            # Get all categories
            categories = SkillCategory.query.all()
            
            # Initialize all categories
            for category in categories:
                categorized_skills[category.name] = []
            
            # Categorize skills
            for skill in skills:
                if skill.category:
                    category_name = skill.category.name
                    if category_name not in categorized_skills:
                        categorized_skills[category_name] = []
                    categorized_skills[category_name].append(skill)
                else:
                    # Uncategorized skills
                    if 'Uncategorized' not in categorized_skills:
                        categorized_skills['Uncategorized'] = []
                    categorized_skills['Uncategorized'].append(skill)
            
            return categorized_skills
            
        except Exception as e:
            raise SkillServiceError(f"Failed to categorize skills: {str(e)}")
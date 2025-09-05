"""
User service for handling user data business logic
"""
from collections import defaultdict
from typing import List, Any, Tuple
from models import UserData, UserSkill, Skill, db

from .skill.skill_service import get_skill_service
from .base_service import BaseService

from utils.forms import validate_user_data_form


class UserService(BaseService):
    """Service for user data operations"""

    def __init__(self)  -> None:
        super().__init__()
        # Get the skill service instance
        self.skill_service = get_skill_service()
    
    def get_user_data(self) -> UserData|None:
        """Get the first (and typically only) user data record"""
        try:
            return UserData.query.first()
        except Exception as e:
            self.logger.error(f"Error getting user data: {str(e)}")
            return None
    
    def create_or_update_user(self, name: str, email: str, phone: str|None = None, linkedin: str|None = None,
                             github: str|None = None, skills: List = []) -> Tuple[bool, UserData|None, str|None]:
        """
        Create or update user data

        Args:
            name: User name
            email: User email
            phone: User phone (optional)
            linkedin: LinkedIn URL (optional)
            github: GitHub URL (optional)

        Returns:
            tuple: (success: bool, user: UserData, error: str)
        """
        # Validate input data
        data = {
            'name': name,
            'email': email,
            'phone': phone or '',
            'linkedin': linkedin or '',
            'github': github or '',
            'skills': skills or '',
        }
        
        is_valid, errors = validate_user_data_form(data)
        if not is_valid:
            error_msg = '; '.join([f"{field}: {errors[0]}" for field, errors in errors.items()])
            return False, None, error_msg
        
        # Get existing user or create new one
        user = self.get_user_data()
        
        if user:
            # Update existing user
            skills = list((" ".join(skills.split())).split(','))
            self.update_user_skills(user_id=user.id, skills=skills)

            return self.update(user, **data)
        else:
            # Create new user
            return self.create(UserData, **data)
    
 
    def validate_user_data(self, data: dict[str, Any]):
        """
        Validate user data
        
        Args:
            data: Dictionary of user data
            
        Returns:
            tuple: (is_valid: bool, errors: dict)
        """
        return validate_user_data_form(data)
    
    def get_user_profile_summary(self):
        """
        Get user profile summary for display
        
        Returns:
            dict: User profile summary
        """
        user = self.get_user_data()
        if not user:
            return {
                'name': 'Not Set',
                'email': 'Not Set',
                'phone': 'Not Set',
                'linkedin': None,
                'github': None,
                'has_profile': False
            }
        
        return {
            'name': user.name or 'Not Set',
            'email': user.email or 'Not Set',
            'phone': user.phone or 'Not Set',
            'linkedin': user.linkedin if user.linkedin else None,
            'github': user.github if user.github else None,
            'has_profile': bool(user.name and user.email)
        }
    
    def export_user_data(self):
        """
        Export user data for backup or transfer
        
        Returns:
            dict: Complete user data
        """
        user = self.get_user_data()
        if not user:
            return {}
        
        return {
            'name': user.name,
            'email': user.email,
            'phone': user.phone,
            'linkedin': user.linkedin,
            'github': user.github,
        }
    
    def import_user_data(self, data):
        """
        Import user data from backup
        
        Args:
            data: Dictionary of user data
            
        Returns:
            tuple: (success: bool, user: UserData, error: str)
        """
        required_fields = ['name', 'email']
        for field in required_fields:
            if field not in data or not data[field]:
                return False, None, f"Missing required field: {field}"
        
        return self.create_or_update_user(
            name=data.get('name'),
            email=data.get('email'),
            phone=data.get('phone'),
            linkedin=data.get('linkedin'),
            github=data.get('github'),

        )


    def update_user_skills(self, user_id: int, skills: List[str]):
        """
        Extract skills from the job description and store them in the JobSkill table.

        :param job_id: ID of the job
        :param job_description: Description of the job
        """

        # determine If all user skills exist in the database
        user_skills = []
        for skill_name in skills:
            name = " ".join([word[0].upper() + word[1:] for word in skill_name.split(" ")])
            skill = self.skill_service.get_skill_by_name(name)

            # if skill does not exist then add it to the db
            if not skill:
                _, skill, _ = self.skill_service.create_skill(name=skill_name)

            user_skills.append(skill)

        # Fetch skills from the db
        #db_user_skills = db.session.execute(db.select(UserSkill).where(UserSkill.user_id == user_id)).all()
        db_user_skills = UserSkill.query.filter_by(user_id=user_id).all()

        list_ids = [skill.id for skill in user_skills]
        # remove skills not longer in user list
        for db_user_skill in db_user_skills:
            if db_user_skill.skill_id not in [skill.id for skill in user_skills]:
                self.delete(db_user_skill)
        
        # add new skills
        for user_skill in user_skills:
            print(user_skill)
            print(type(user_skill))
            if user_skill not in db_user_skills:
                self.create(UserSkill, **{
                    'user_id': user_id,
                    'skill_id': user_skill.id
                })

        return True, user_skills

    def get_user_skills(self, user_id):
        query = UserData.query

        user = query.filter(UserData.id == user_id).first()

        skills = list(user.skills)

        return skills
    
    def get_user_skills_by_category(self, user_id, get_blacklisted=False):
        user = UserData.query.filter(UserData.id == user_id).first()

        if not user:
            return {}

        skills_by_category = defaultdict(list)

        # Use your association proxy to get skills directly
        for skill in user.skills:  # Using your Job -> Skill association proxy
            category = skill.skill_category

            category_name = "Uncategorized" if not category else category.name

            if get_blacklisted:
                skills_by_category[category_name].append(skill.name)
            elif not skill.is_blacklisted:  # Fixed condition
                skills_by_category[category_name].append(skill.name)

        return dict(skills_by_category)
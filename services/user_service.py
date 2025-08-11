"""
User service for handling user data business logic
"""
from models import UserData
from .base_service import BaseService
from utils.forms import validate_user_data_form


class UserService(BaseService):
    """Service for user data operations"""
    
    def get_user_data(self):
        """Get the first (and typically only) user data record"""
        try:
            return UserData.query.first()
        except Exception as e:
            self.logger.error(f"Error getting user data: {str(e)}")
            return None
    
    def create_or_update_user(self, name, email, phone=None, linkedin=None, 
                             github=None, skills=None):
        """
        Create or update user data
        
        Args:
            name: User name
            email: User email
            phone: User phone (optional)
            linkedin: LinkedIn URL (optional)
            github: GitHub URL (optional)
            skills: Skills string (optional)
            
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
            'skills': skills or ''
        }
        
        is_valid, errors = validate_user_data_form(data)
        if not is_valid:
            error_msg = '; '.join([f"{field}: {errors[0]}" for field, errors in errors.items()])
            return False, None, error_msg
        
        # Get existing user or create new one
        user = self.get_user_data()
        
        if user:
            # Update existing user
            return self.update(user, **data)
        else:
            # Create new user
            return self.create(UserData, **data)
    
    def update_user_skills(self, skills):
        """
        Update user skills
        
        Args:
            skills: Skills string
            
        Returns:
            tuple: (success: bool, user: UserData, error: str)
        """
        user = self.get_user_data()
        if not user:
            return False, None, "User not found"
        
        return self.update(user, skills=skills)
    
    def get_user_skills(self):
        """
        Get user skills as a string
        
        Returns:
            str: User skills or empty string
        """
        user = self.get_user_data()
        return user.skills if user and user.skills else ""
    
    def validate_user_data(self, data):
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
                'skills_count': 0,
                'has_profile': False
            }
        
        skills_count = 0
        if user.skills:
            skills_count = len([skill.strip() for skill in user.skills.split(',') if skill.strip()])
        
        return {
            'name': user.name or 'Not Set',
            'email': user.email or 'Not Set',
            'phone': user.phone or 'Not Set',
            'linkedin': user.linkedin if user.linkedin else None,
            'github': user.github if user.github else None,
            'skills_count': skills_count,
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
            'skills': user.skills
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
            skills=data.get('skills')
        )

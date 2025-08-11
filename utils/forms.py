"""
Form validation and processing utilities
"""
from flask import request
from wtforms.validators import ValidationError
from models import ApplicationStatus, JobMode
import re
from urllib.parse import urlparse


def validate_url(url):
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid URL, False otherwise
    """
    if not url:
        return True  # Optional field
    
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_email(email):
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        bool: True if valid email, False otherwise
    """
    if not email:
        return True  # Optional field
    
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None


def validate_phone(phone):
    """
    Validate phone number format (flexible)
    
    Args:
        phone: Phone string to validate
        
    Returns:
        bool: True if valid phone, False otherwise
    """
    if not phone:
        return True  # Optional field
    
    # Remove common separators and spaces
    cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check if it contains only digits and is reasonable length
    return cleaned_phone.isdigit() and 7 <= len(cleaned_phone) <= 15


def validate_skills_string(skills):
    """
    Validate skills string format (comma-separated)
    
    Args:
        skills: Skills string to validate
        
    Returns:
        tuple: (is_valid: bool, cleaned_skills: str)
    """
    if not skills:
        return True, ""
    
    # Split by comma and clean up
    skill_list = [skill.strip() for skill in skills.split(',') if skill.strip()]
    
    # Check for reasonable number of skills
    if len(skill_list) > 50:
        return False, skills
    
    # Check individual skill length
    for skill in skill_list:
        if len(skill) > 100:
            return False, skills
    
    # Return cleaned skills string
    cleaned_skills = ', '.join(skill_list)
    return True, cleaned_skills


def get_form_errors(form):
    """
    Extract form errors into a dictionary
    
    Args:
        form: WTForms form instance
        
    Returns:
        dict: Dictionary of field errors
    """
    errors = {}
    for field_name, field_errors in form.errors.items():
        errors[field_name] = field_errors
    return errors


def populate_job_form_choices(form):
    """
    Populate dynamic choices for job form
    
    Args:
        form: JobForm instance
    """
    # Populate job mode choices
    job_mode_choices = [('', 'Select job mode')]
    job_mode_choices.extend([(mode.value, mode.value) for mode in JobMode])
    form.job_mode.choices = job_mode_choices


def populate_log_form_choices(form):
    """
    Populate dynamic choices for log form
    
    Args:
        form: LogForm instance
    """
    # Populate status change choices
    status_choices = [('', 'No status change')]
    status_choices.extend([(status.value, status.value) for status in ApplicationStatus])
    form.status_change.choices = status_choices


def clean_text_input(text, max_length=None):
    """
    Clean and sanitize text input
    
    Args:
        text: Input text to clean
        max_length: Maximum allowed length
        
    Returns:
        str: Cleaned text
    """
    if not text:
        return ""
    
    # Strip whitespace
    cleaned = text.strip()
    
    # Remove excessive whitespace
    cleaned = re.sub(r'\s+', ' ', cleaned)
    
    # Truncate if necessary
    if max_length and len(cleaned) > max_length:
        cleaned = cleaned[:max_length].strip()
    
    return cleaned


def extract_form_data(form_fields):
    """
    Extract and clean form data from request
    
    Args:
        form_fields: List of field names to extract
        
    Returns:
        dict: Dictionary of cleaned form data
    """
    data = {}
    
    for field in form_fields:
        value = request.form.get(field, '').strip()
        data[field] = clean_text_input(value)
    
    return data


def validate_job_form_data(data):
    """
    Validate job form data
    
    Args:
        data: Dictionary of form data
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    # Required fields
    if not data.get('company'):
        errors['company'] = ['Company name is required']
    
    if not data.get('title'):
        errors['title'] = ['Job title is required']
    
    # URL validation
    if data.get('url') and not validate_url(data['url']):
        errors['url'] = ['Please enter a valid URL']
    
    # Job mode validation
    if data.get('job_mode'):
        valid_modes = [mode.value for mode in JobMode]
        if data['job_mode'] not in valid_modes:
            errors['job_mode'] = ['Please select a valid job mode']
    
    return len(errors) == 0, errors


def validate_user_data_form(data):
    """
    Validate user data form
    
    Args:
        data: Dictionary of form data
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    # Required fields
    if not data.get('name'):
        errors['name'] = ['Name is required']
    
    if not data.get('email'):
        errors['email'] = ['Email is required']
    
    # Email validation
    if data.get('email') and not validate_email(data['email']):
        errors['email'] = ['Please enter a valid email address']
    
    # Phone validation
    if data.get('phone') and not validate_phone(data['phone']):
        errors['phone'] = ['Please enter a valid phone number']
    
    # URL validations
    for url_field in ['linkedin', 'github']:
        if data.get(url_field) and not validate_url(data[url_field]):
            errors[url_field] = [f'Please enter a valid {url_field.title()} URL']
    
    # Skills validation
    if data.get('skills'):
        is_valid, cleaned_skills = validate_skills_string(data['skills'])
        if not is_valid:
            errors['skills'] = ['Skills format is invalid. Please use comma-separated values.']
        else:
            data['skills'] = cleaned_skills
    
    return len(errors) == 0, errors


def validate_log_form_data(data):
    """
    Validate log form data
    
    Args:
        data: Dictionary of form data
        
    Returns:
        tuple: (is_valid: bool, errors: dict)
    """
    errors = {}
    
    # Required fields
    if not data.get('note'):
        errors['note'] = ['Log note is required']
    
    # Note length validation
    if data.get('note') and len(data['note']) > 1000:
        errors['note'] = ['Note cannot exceed 1000 characters']
    
    # Status change validation
    if data.get('status_change'):
        valid_statuses = [status.value for status in ApplicationStatus]
        if data['status_change'] not in valid_statuses:
            errors['status_change'] = ['Please select a valid status']
    
    return len(errors) == 0, errors


class CustomValidators:
    """Custom validators for WTForms"""
    
    @staticmethod
    def validate_job_mode(form, field):
        """Validate job mode field"""
        if field.data:
            valid_modes = [mode.value for mode in JobMode]
            if field.data not in valid_modes:
                raise ValidationError('Please select a valid job mode')
    
    @staticmethod
    def validate_status_change(form, field):
        """Validate status change field"""
        if field.data:
            valid_statuses = [status.value for status in ApplicationStatus]
            if field.data not in valid_statuses:
                raise ValidationError('Please select a valid status')
    
    @staticmethod
    def validate_skills_format(form, field):
        """Validate skills format"""
        if field.data:
            is_valid, _ = validate_skills_string(field.data)
            if not is_valid:
                raise ValidationError('Skills format is invalid. Please use comma-separated values.')

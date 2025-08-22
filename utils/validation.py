"""
Common validation utilities with type hints
"""
import re
from typing import Optional, Tuple, List, Dict, Any, Union
from urllib.parse import urlparse
from models import ApplicationStatus, JobMode


class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass


class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool, value: Any = None, errors: List[str] = None):
        self.is_valid = is_valid
        self.value = value
        self.errors = errors or []
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def add_error(self, error: str) -> None:
        """Add an error to the result"""
        self.errors.append(error)
        self.is_valid = False


def validate_required_string(value: Any, field_name: str, min_length: int = 1, max_length: int = 500) -> ValidationResult:
    """
    Validate a required string field
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        min_length: Minimum length required
        max_length: Maximum length allowed
        
    Returns:
        ValidationResult: Validation result with cleaned value
    """
    if value is None:
        return ValidationResult(False, None, [f"{field_name} is required"])
    
    # Convert to string and strip whitespace
    str_value = str(value).strip()
    
    if len(str_value) < min_length:
        return ValidationResult(False, None, [f"{field_name} must be at least {min_length} characters"])
    
    if len(str_value) > max_length:
        return ValidationResult(False, None, [f"{field_name} must be no more than {max_length} characters"])
    
    return ValidationResult(True, str_value)


def validate_optional_string(value: Any, field_name: str, max_length: int = 500) -> ValidationResult:
    """
    Validate an optional string field
    
    Args:
        value: Value to validate
        field_name: Name of the field for error messages
        max_length: Maximum length allowed
        
    Returns:
        ValidationResult: Validation result with cleaned value
    """
    if value is None or str(value).strip() == "":
        return ValidationResult(True, None)
    
    str_value = str(value).strip()
    
    if len(str_value) > max_length:
        return ValidationResult(False, None, [f"{field_name} must be no more than {max_length} characters"])
    
    return ValidationResult(True, str_value)


def validate_email(email: Optional[str]) -> ValidationResult:
    """
    Validate email format
    
    Args:
        email: Email string to validate
        
    Returns:
        ValidationResult: Validation result
    """
    if not email or not email.strip():
        return ValidationResult(True, None)  # Optional field
    
    email = email.strip().lower()
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        return ValidationResult(False, None, ["Please enter a valid email address"])
    
    return ValidationResult(True, email)


def validate_phone(phone: Optional[str]) -> ValidationResult:
    """
    Validate phone number format (flexible)
    
    Args:
        phone: Phone string to validate
        
    Returns:
        ValidationResult: Validation result
    """
    if not phone or not phone.strip():
        return ValidationResult(True, None)  # Optional field
    
    phone = phone.strip()
    
    # Remove common separators and spaces
    cleaned_phone = re.sub(r'[\s\-\(\)\+\.]', '', phone)
    
    # Check if it contains only digits and is reasonable length
    if not cleaned_phone.isdigit() or not (7 <= len(cleaned_phone) <= 15):
        return ValidationResult(False, None, ["Please enter a valid phone number"])
    
    return ValidationResult(True, phone)


def validate_url(url: Optional[str]) -> ValidationResult:
    """
    Validate URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        ValidationResult: Validation result
    """
    if not url or not url.strip():
        return ValidationResult(True, None)  # Optional field
    
    url = url.strip()
    
    try:
        result = urlparse(url)
        if not all([result.scheme, result.netloc]):
            return ValidationResult(False, None, ["Please enter a valid URL"])
        
        if result.scheme not in ['http', 'https']:
            return ValidationResult(False, None, ["URL must use http or https"])
        
        return ValidationResult(True, url)
        
    except Exception:
        return ValidationResult(False, None, ["Please enter a valid URL"])


def validate_enum_value(value: Optional[str], enum_class: type, field_name: str, required: bool = False) -> ValidationResult:
    """
    Validate enum value
    
    Args:
        value: Value to validate
        enum_class: Enum class to validate against
        field_name: Name of the field for error messages
        required: Whether the field is required
        
    Returns:
        ValidationResult: Validation result
    """
    if not value or not value.strip():
        if required:
            return ValidationResult(False, None, [f"{field_name} is required"])
        return ValidationResult(True, None)
    
    value = value.strip()
    valid_values = [item.value for item in enum_class]
    
    if value not in valid_values:
        return ValidationResult(False, None, [f"{field_name} must be one of: {', '.join(valid_values)}"])
    
    return ValidationResult(True, value)





def validate_job_data(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, List[str]]]:
    """
    Validate job application data
    
    Args:
        data: Dictionary of job data
        
    Returns:
        Tuple[bool, Dict[str, Any], Dict[str, List[str]]]: (is_valid, cleaned_data, errors)
    """
    errors = {}
    cleaned_data = {}
    
    # Validate required fields
    company_result = validate_required_string(data.get('company'), 'Company name', max_length=100)
    if not company_result:
        errors['company'] = company_result.errors
    else:
        cleaned_data['company'] = company_result.value
    
    title_result = validate_required_string(data.get('title'), 'Job title', max_length=200)
    if not title_result:
        errors['title'] = title_result.errors
    else:
        cleaned_data['title'] = title_result.value
    
    # Validate optional fields
    description_result = validate_optional_string(data.get('description'), 'Description', max_length=10000)
    if not description_result:
        errors['description'] = description_result.errors
    else:
        cleaned_data['description'] = description_result.value
    
    url_result = validate_url(data.get('url'))
    if not url_result:
        errors['url'] = url_result.errors
    else:
        cleaned_data['url'] = url_result.value
    
    location_result = validate_optional_string(data.get('office_location'), 'Office location', max_length=200)
    if not location_result:
        errors['office_location'] = location_result.errors
    else:
        cleaned_data['office_location'] = location_result.value
    
    country_result = validate_optional_string(data.get('country'), 'Country', max_length=100)
    if not country_result:
        errors['country'] = country_result.errors
    else:
        cleaned_data['country'] = country_result.value
    
    job_mode_result = validate_enum_value(data.get('job_mode'), JobMode, 'Job mode')
    if not job_mode_result:
        errors['job_mode'] = job_mode_result.errors
    else:
        cleaned_data['job_mode'] = job_mode_result.value
    
    is_valid = len(errors) == 0
    return is_valid, cleaned_data, errors


def validate_user_data(data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], Dict[str, List[str]]]:
    """
    Validate user profile data
    
    Args:
        data: Dictionary of user data
        
    Returns:
        Tuple[bool, Dict[str, Any], Dict[str, List[str]]]: (is_valid, cleaned_data, errors)
    """
    errors = {}
    cleaned_data = {}
    
    # Validate required fields
    name_result = validate_required_string(data.get('name'), 'Name', max_length=100)
    if not name_result:
        errors['name'] = name_result.errors
    else:
        cleaned_data['name'] = name_result.value
    
    email_result = validate_email(data.get('email'))
    if not email_result:
        errors['email'] = email_result.errors
    else:
        cleaned_data['email'] = email_result.value
    
    # Validate optional fields
    phone_result = validate_phone(data.get('phone'))
    if not phone_result:
        errors['phone'] = phone_result.errors
    else:
        cleaned_data['phone'] = phone_result.value
    
    linkedin_result = validate_url(data.get('linkedin'))
    if not linkedin_result:
        errors['linkedin'] = linkedin_result.errors
    else:
        cleaned_data['linkedin'] = linkedin_result.value
    
    github_result = validate_url(data.get('github'))
    if not github_result:
        errors['github'] = github_result.errors
    else:
        cleaned_data['github'] = github_result.value
    

    
    is_valid = len(errors) == 0
    return is_valid, cleaned_data, errors

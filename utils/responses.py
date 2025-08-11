"""
Response utility functions for consistent API responses and error handling
"""
from flask import jsonify, flash, current_app
import logging


def success_response(message, data=None, status_code=200):
    """
    Create a standardized success response
    
    Args:
        message: Success message
        data: Optional data to include
        status_code: HTTP status code (default: 200)
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': True,
        'message': message
    }
    
    if data:
        response.update(data)
    
    return jsonify(response), status_code


def error_response(message, error_details=None, status_code=400):
    """
    Create a standardized error response
    
    Args:
        message: Error message
        error_details: Optional detailed error information
        status_code: HTTP status code (default: 400)
        
    Returns:
        tuple: (response, status_code)
    """
    response = {
        'success': False,
        'error': message
    }
    
    if error_details:
        response['details'] = error_details
    
    # Log the error
    current_app.logger.error(f"API Error: {message} - Details: {error_details}")
    
    return jsonify(response), status_code


def validation_error_response(form_errors):
    """
    Create a response for form validation errors
    
    Args:
        form_errors: Dictionary of form field errors
        
    Returns:
        tuple: (response, status_code)
    """
    return error_response(
        message="Validation failed",
        error_details=form_errors,
        status_code=422
    )


def flash_success(message, category='success'):
    """
    Flash a success message with consistent formatting
    
    Args:
        message: Success message
        category: Flash message category (default: 'success')
    """
    flash(message, category)


def flash_error(message, category='error'):
    """
    Flash an error message with consistent formatting
    
    Args:
        message: Error message
        category: Flash message category (default: 'error')
    """
    flash(message, category)


def flash_warning(message, category='warning'):
    """
    Flash a warning message with consistent formatting
    
    Args:
        message: Warning message
        category: Flash message category (default: 'warning')
    """
    flash(message, category)


def flash_info(message, category='info'):
    """
    Flash an info message with consistent formatting
    
    Args:
        message: Info message
        category: Flash message category (default: 'info')
    """
    flash(message, category)


def handle_scraping_response(scraping_result):
    """
    Handle web scraping results and return appropriate response
    
    Args:
        scraping_result: Result from scraping operation
        
    Returns:
        dict: Response data for AJAX requests
    """
    if scraping_result and len(scraping_result) == 3:
        title, company, description = scraping_result
        
        if title or company or description:
            response_data = {
                'success': True,
                'message': 'Job details scraped successfully!'
            }
            
            if title:
                response_data['title'] = title
            if company:
                response_data['company'] = company
            if description:
                response_data['description'] = description
                
            return response_data
    
    return {
        'success': False,
        'error': 'Failed to scrape job details. Please fill in the information manually.'
    }


def handle_job_match_response(match_result):
    """
    Handle job matching analysis results
    
    Args:
        match_result: Result from job matching analysis
        
    Returns:
        dict: Formatted match data
    """
    if match_result and len(match_result) == 3:
        match_score, matched_keywords, unmatched_keywords = match_result
        
        return {
            'match_score': match_score,
            'matched_keywords': matched_keywords,
            'unmatched_keywords': unmatched_keywords
        }
    
    return {
        'match_score': 0,
        'matched_keywords': [],
        'unmatched_keywords': []
    }


def log_and_flash_error(error_message, flash_message=None, log_level=logging.ERROR):
    """
    Log an error and optionally flash a user-friendly message
    
    Args:
        error_message: Technical error message for logging
        flash_message: User-friendly message for flash (optional)
        log_level: Logging level (default: ERROR)
    """
    current_app.logger.log(log_level, error_message)
    
    if flash_message:
        flash_error(flash_message)


def safe_int_conversion(value, default=None):
    """
    Safely convert a value to integer
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        int or default: Converted integer or default value
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_str_conversion(value, default=""):
    """
    Safely convert a value to string
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        
    Returns:
        str: Converted string or default value
    """
    try:
        return str(value) if value is not None else default
    except Exception:
        return default


def format_file_size(size_bytes):
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def sanitize_filename(filename):
    """
    Sanitize filename for safe file operations
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    filename = filename.strip(' .')
    
    # Ensure filename is not empty
    if not filename:
        filename = "untitled"
    
    return filename

import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime


class LoggingManager:
    """Centralized logging configuration and management"""
    
    def __init__(self, app=None):
        self.app = app
        self._handlers = []
        
    def init_app(self, app):
        """Initialize logging for the Flask app"""
        self.app = app
        self._setup_logging()
        
    def _setup_logging(self):
        """Configure logging based on app configuration"""
        if not self.app:
            return
            
        # Clear existing handlers to avoid duplicates
        self._clear_existing_handlers()
        
        # Configure based on environment
        if self.app.debug or self.app.testing:
            self._setup_development_logging()
        else:
            self._setup_production_logging()
            
        # Log application startup
        self.app.logger.info('Job Application Manager startup')
        
    def _clear_existing_handlers(self):
        """Remove existing handlers to prevent duplicates"""
        for handler in self.app.logger.handlers[:]:
            self.app.logger.removeHandler(handler)
            
    def _setup_development_logging(self):
        """Setup logging for development environment"""
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(console_formatter)
        
        self.app.logger.addHandler(console_handler)
        self.app.logger.setLevel(logging.DEBUG)
        self._handlers.append(console_handler)
        
    def _setup_production_logging(self):
        """Setup logging for production environment"""
        # Ensure logs directory exists
        log_folder = self.app.config.get('LOG_FOLDER', 'logs')
        if not os.path.exists(log_folder):
            os.makedirs(log_folder, exist_ok=True)
            
        # File handler for production
        log_file = os.path.join(log_folder, 'job_app.log')
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=self.app.config.get('LOG_MAX_BYTES', 10485760),  # 10MB default
            backupCount=self.app.config.get('LOG_BACKUP_COUNT', 10)
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(file_formatter)
        file_handler.setLevel(self.app.config.get('LOG_LEVEL', logging.INFO))
        
        self.app.logger.addHandler(file_handler)
        self.app.logger.setLevel(self.app.config.get('LOG_LEVEL', logging.INFO))
        self._handlers.append(file_handler)
        
        # Optional: Add error-only handler for critical issues
        error_file = os.path.join(log_folder, 'errors.log')
        error_handler = RotatingFileHandler(
            error_file,
            maxBytes=self.app.config.get('LOG_MAX_BYTES', 10485760),
            backupCount=self.app.config.get('LOG_BACKUP_COUNT', 5)
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(file_formatter)
        
        self.app.logger.addHandler(error_handler)
        self._handlers.append(error_handler)
        
    def log_request_info(self, request):
        """Log request information for security monitoring"""
        if not self.app.debug:
            self.app.logger.info(
                f"Request: {request.method} {request.url} from {request.remote_addr}"
            )
            
    def log_error(self, error, context=None):
        """Log error with optional context"""
        error_msg = f"Error: {error}"
        if context:
            error_msg += f" | Context: {context}"
        self.app.logger.error(error_msg)
        
    def log_security_event(self, event_type, details, request=None):
        """Log security-related events"""
        msg = f"Security Event: {event_type} - {details}"
        if request:
            msg += f" | IP: {request.remote_addr} | URL: {request.url}"
        self.app.logger.warning(msg)
        
    def cleanup(self):
        """Clean up handlers"""
        for handler in self._handlers:
            try:  
                handler.close()  
                if self.app:  
                    self.app.logger.removeHandler(handler)  
            except Exception:  
                pass
        self._handlers.clear()


# Global logging manager instance
logging_manager = LoggingManager()
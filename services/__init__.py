# Services package with conditional imports to handle missing dependencies

# Core services that don't depend on spacy
from .user_service import UserService
from .template_service import TemplateService
from .log_service import LogService

from .job_service import JobService
from .skill_extraction_service import SkillExtractionService, SkillExtractionServiceSingleton
from .skill_matching_service import SkillMatchingService
from .enhanced_skill_service import EnhancedSkillService
from .industry_service import IndustryService
from .skill_blacklist_service import SkillBlacklistService

# Services that don't depend on spacy but might depend on the above
from .category_service import CategoryService

# Pre-initialize the skill extraction singleton to improve performance
def initialize_skill_services():
    """Initialize skill extraction services for better performance"""
    try:
        singleton = SkillExtractionServiceSingleton()
        singleton.initialize()
        return True
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to pre-initialize skill services: {str(e)}")
        return False

__all__ = [
    'JobService',
    'UserService',
    'TemplateService',
    'LogService',
    'SkillExtractionService',
    'SkillMatchingService',
    'initialize_skill_services',
    'EnhancedSkillService',
    'IndustryService',
    'SkillBlacklistService',
    'CategoryService',
]

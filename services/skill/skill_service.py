from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import SQLAlchemyError
from models import Skill, SkillCategory, SkillVariant, JobSkill, db
from utils.forms import sanitize_input

from configurations.skill_config import SkillExtractionConfig
from dtos.skill_dtos import ProcessedSkillsResult

from ..base_service import BaseService
from services.skill.skill_lookup_service import SkillLookupService
from services.skill.skill_extractor import SkillExtractor
from services.skill.skill_normalizer import SkillNormalizer
from services.skill.skill_categorizer import SkillCategorizer

class SkillService(BaseService):
    """Main skill service using SQLAlchemy ORM models directly"""
    
    def __init__(self):
        super().__init__()
        self.config = SkillExtractionConfig()
        self.lookup_service = SkillLookupService()
        self.extractor = SkillExtractor(self.config)
        self.normalizer = SkillNormalizer(self.lookup_service, self.config)
        self.categorizer = SkillCategorizer()
    
    # =============================================================================
    # Main Processing Methods
    # =============================================================================
    
    def process_job_description(self, job_description: str) -> ProcessedSkillsResult:
        """Complete skill processing pipeline for job descriptions"""
        try:
            # Step 1: Extract skills from text
            extraction_result = self.extractor.extract_skills_from_text(job_description)
            if not extraction_result.success:
                return ProcessedSkillsResult(
                    extracted_skills=[],
                    normalized_skills=[],
                    unmatched_skills=[],
                    categorized_skills={},
                    total_skills=0,
                    success=False,
                    error=extraction_result.error
                )
            
            # Step 2: Normalize extracted skills
            normalization_result = self.normalizer.normalize_skills(extraction_result.skills)
            if not normalization_result.success:
                return ProcessedSkillsResult(
                    extracted_skills=extraction_result.skills,
                    normalized_skills=[],
                    unmatched_skills=[],
                    categorized_skills={},
                    total_skills=extraction_result.total_skills,
                    success=False,
                    error=normalization_result.error
                )
            
            # Step 3: Categorize normalized skills
            categorized_skills = self.categorizer.categorize_skills(normalization_result.normalized_skills)
            
            return ProcessedSkillsResult(
                extracted_skills=extraction_result.skills,
                normalized_skills=normalization_result.normalized_skills,
                unmatched_skills=normalization_result.unmatched_skills,
                categorized_skills=categorized_skills,
                total_skills=len(normalization_result.normalized_skills)+len(normalization_result.unmatched_skills),
                success=True
            )
            
        except Exception as e:
            return ProcessedSkillsResult(
                extracted_skills=[],
                normalized_skills=[],
                unmatched_skills=[],
                categorized_skills={},
                total_skills=0,
                success=False,
                error=f"Processing failed: {str(e)}"
            )
    
    # =============================================================================
    # CRUD Operations using SQLAlchemy ORM
    # =============================================================================
    
    def get_skill_by_id(self, skill_id: int, include_relationships: bool = False) -> Optional[Skill]:
        """Get skill by ID"""
        try:
            opts = ()  
            if include_relationships:  
                opts = (joinedload(Skill.category), joinedload(Skill.variants))  
            return db.session.get(Skill, skill_id, options=opts)

        except SQLAlchemyError as e:
            self.logger.error("Database error getting skill by ID %s: %s", skill_id, e, exc_info=True)  
            return None
    
    def get_skill_by_name(self, skill_name: str) -> Optional[Skill]:
        """Get skill by name"""
        result = self.filter_by(Skill, order_by=None, **{"name": skill_name})
        return result[0] if result else None

    def get_all_skills(self, order_by=None, include_relationships: bool = False) -> List[Skill]:
        """Get all existing skills"""
        try:
            query = Skill.query
            
            if include_relationships:
                query = query.options(
                    joinedload(Skill.category),
                    joinedload(Skill.variants))
            
            if order_by is None:
                query = query.order_by(Skill.name)
            else:
                query = query.order_by(order_by)
            
            return query.all()
            
        except SQLAlchemyError as e:
            self.logger.error("Database error getting all skills: %s", e, exc_info=True)  
            return []

    def get_all_active_skills(self, order_by=None, include_relationships: bool = False) -> List[Skill]:
        """Get all non-blacklisted skills"""
        try:
            query = Skill.query.filter_by(is_blacklisted=False)
            
            if include_relationships:
                query = query.options(
                    joinedload(Skill.category),
                    joinedload(Skill.variants))
            
            if order_by is None:
                query = query.order_by(Skill.name)
            else:
                query = query.order_by(order_by)
            
            return query.all()
            
        except SQLAlchemyError as e:
            self.logger.error("Database error getting all active skills: %s", e, exc_info=True) 
            return []
    
    def get_all_skills_and_category(self) -> List[dict]:
        """Get all skills with their category information"""
        try:
            # Use SQLAlchemy ORM join with outerjoin for left join
            results = db.session.query(Skill, SkillCategory).outerjoin(
                SkillCategory, Skill.category_id == SkillCategory.id
            ).filter(Skill.is_blacklisted == False).all()
            
            skills_list = []
            for skill, category in results:
                skills_list.append({
                    'id': skill.id,
                    'name': skill.name,
                    'category_id': category.id if category else None,
                    'category_name': category.name if category else ''
                })
            
            return skills_list
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting skills with categories: {e}", exc_info=True)
            return []
    
    def get_uncategorized_skills(self) -> List[dict]:
        """Get skills without categories"""
        try:
            skills = Skill.query.filter(
                Skill.category_id.is_(None),
                Skill.is_blacklisted.is_(False)
            ).all()
            
            return [{'id': skill.id, 'name': skill.name} for skill in skills]
            
        except SQLAlchemyError as e:
            self.logger.error(f"Database error getting uncategorized skills: {e}", exc_info=True)
            return []
    
    def get_blacklist_skills(self, order_by=None) -> List[Skill]:
        """Get blacklisted skills"""
        try:
            query = Skill.query.filter_by(is_blacklisted=True)
            
            if order_by is None:
                query = query.order_by(Skill.name.desc())
            else:
                query = query.order_by(order_by)
            
            return query.all()
            
        except SQLAlchemyError as e:
            self.logger.error("Database error getting blacklisted skills: %s", e, exc_info=True)
            return []
    
    def create_skill(self, name: str, category: Optional[int] = None, is_blacklisted: bool = False) -> Tuple[bool, Optional[Skill], Optional[str]]:
        """Create a new skill"""
        try:
            # Validate and sanitize inputs
            if not name or not name.strip():
                return False, None, "Name is required"
            
            name = sanitize_input(name)
            
            # Check if skill already exists
            existing_skill = Skill.query.filter_by(name=name).first()
            if existing_skill:
                return False, None, f"Skill '{name}' already exists"
            
            # Create new skill
            skill = Skill(
                name=name,
                category_id=category,
                is_blacklisted=is_blacklisted
            )
            
            db.session.add(skill)
            db.session.commit()
            
            # Refresh lookup cache
            self.lookup_service.refresh()
            
            return True, skill, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, None, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            return False, None, f"Validation error: {str(e)}"
    
    def update_skill(self, skill_id: int, **kwargs) -> Tuple[bool, Optional[Skill], Optional[str]]:
        """Update a skill"""
        try:
            skill = Skill.query.get(skill_id)
            if not skill:
                return False, None, "Skill not found"
            
            proposed_name = kwargs.get('name')  
            if proposed_name:  
                proposed_name = sanitize_input(proposed_name)
                dupe = Skill.query.filter(  
                    Skill.id != skill_id,  
                    Skill.name.ilike(proposed_name)  
                ).first()
                if dupe:  
                    return False, None, f"Skill '{proposed_name}' already exists"
            
            # Update attributes
            for key, value in kwargs.items():                    
                if hasattr(skill, key):
                    if key == 'name' and value:  
                        value = proposed_name
                    setattr(skill, key, value)
            
            db.session.commit()
            
            # Refresh lookup cache
            self.lookup_service.refresh()
            
            return True, skill, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Database error during skill update: {e}", exc_info=True)
            return False, None, f"Database error: {str(e)}"
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error during skill update: {e}", exc_info=True)
            return False, None, f"Update error: {str(e)}"
    
    def delete_skill(self, skill_id: int) -> Tuple[bool, bool, Optional[str]]:
        """Delete a skill"""
        try:
            skill = Skill.query.get(skill_id)
            if not skill:
                return False, False, "Skill not found"
            
            db.session.delete(skill)
            db.session.commit()
            
            # Refresh lookup cache
            self.lookup_service.refresh()
            
            return True, True, None
            
        except SQLAlchemyError as e:
            db.session.rollback()
            return False, False, f"Database error: {str(e)}"
    
    def set_blacklist(self, skill_id: int, value: bool) -> Tuple[bool, Optional[Skill], Optional[str]]:
        """Set blacklist status for a skill"""
        return self.update_skill(skill_id, is_blacklisted=value)
    
    # =============================================================================
    # Utility Methods
    # =============================================================================
    
    def refresh_cache(self):
        """Refresh all caches"""
        self.lookup_service.refresh()
    
    def normalize_skill_name(self, extracted_name: str) -> Optional[Skill]:
        """Given an extracted skill name, return the canonical skill object"""
        return self.lookup_service.find_skill(extracted_name)
    
    def normalize_extracted_skills(self, raw_skills_list: List[str]) -> Tuple[List[Skill], List[str]]:
        """Take a list of raw skill names and return normalized Skill objects"""
        result = self.normalizer.normalize_skills(raw_skills_list)
        if result.success:
            return result.normalized_skills, result.unmatched_skills
        else:
            return [], raw_skills_list
    
    def audit_existing_job_skills(self) -> dict:
        """Audit existing job skills for blacklisted items"""
        try:
            # Use SQLAlchemy ORM join
            job_skills = JobSkill.query.join(Skill).all()
            
            blacklisted_found = []
            active_skills = []
            
            for job_skill in job_skills:
                if job_skill.skill.is_blacklisted:
                    blacklisted_found.append({
                        'job_id': job_skill.job_id,
                        'skill_name': job_skill.skill.name,
                        'skill_id': job_skill.skill.id
                    })
                else:
                    active_skills.append(job_skill)
            
            return {
                'total_processed': len(job_skills),
                'active_skills': len(active_skills),
                'blacklisted_found': len(blacklisted_found),
                'blacklisted_details': blacklisted_found
            }
            
        except SQLAlchemyError as e:
            return {
                'total_processed': 0,
                'active_skills': 0,
                'blacklisted_found': 0,
                'blacklisted_details': [],
                'error': f"Audit failed: {str(e)}"
            }
        
# =============================================================================
# Singleton Pattern for Global Access (Optional)
# =============================================================================
# Singleton instance if you need global access
_skill_service_instance = None

def get_skill_service() -> SkillService:
    """Get or create the singleton SkillService instance"""
    global _skill_service_instance
    if _skill_service_instance is None:
        _skill_service_instance = SkillService()
    return _skill_service_instance
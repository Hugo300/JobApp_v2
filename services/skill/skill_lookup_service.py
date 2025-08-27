from typing import Dict, Optional
import logging

from models import Skill, SkillVariant, db

logger = logging.getLogger(__name__)

class SkillLookupService:
    """Service for skill lookup and caching"""
    
    def __init__(self):
        self._skill_lookup: Dict[str, Skill] = {}
        self._build_lookup()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def _build_lookup(self):
        """Build lookup dictionary from database"""
        try:
            self._skill_lookup = {}
            
            # Add canonical skills
            skills = Skill.query.all()
            for skill in skills:
                self._skill_lookup[skill.name.lower()] = skill
                # Keep original case for exact matches
                if skill.name.lower() != skill.name:
                    self._skill_lookup[skill.name] = skill
            
            # Add variants
            variants = SkillVariant.query.join(Skill).all()
            for variant in variants:
                self._skill_lookup[variant.variant_name.lower()] = variant.skill
                # Keep original case
                if variant.variant_name.lower() != variant.variant_name:
                    self._skill_lookup[variant.variant_name] = variant.skill
                    
        except Exception as e:
            self.logger.warning(f"Failed to build skill lookup: {str(e)}", exc_info=True)
            self._skill_lookup = {}
    
    def find_skill(self, name: str) -> Optional[Skill]:
        """Find a skill by name (case-insensitive)"""
        # Try exact match first
        if name in self._skill_lookup:
            return self._skill_lookup[name]
        
        # Try case-insensitive
        if name.lower() in self._skill_lookup:
            return self._skill_lookup[name.lower()]
        
        return None
    
    def refresh(self):
        """Refresh the lookup cache"""
        self._build_lookup()
    
    @property
    def lookup_dict(self) -> Dict[str, Skill]:
        """Get the current lookup dictionary"""
        return self._skill_lookup.copy()

from typing import Dict, Optional
import logging
from flask import current_app
from sqlalchemy.exc import SQLAlchemyError
from types import MappingProxyType

from models import Skill, SkillVariant, db

logger = logging.getLogger(__name__)

class SkillLookupService:
    """Service for skill lookup and caching"""
    
    def __init__(self):
        self._skill_lookup: Dict[str, Skill] = {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._build_lookup()
    
    def _build_lookup(self):
        """Build lookup dictionary from database"""
        try:
            new_lookup: Dict[str, Skill] = {}

            # Read-only ops; avoid nested transactions  
            with db.session.no_autoflush:           
                # Add canonical skills
                skills = Skill.query.all()
                for skill in skills:
                    new_lookup[skill.name.lower()] = skill
                    # Keep original case for exact matches
                    if skill.name.lower() != skill.name:
                        new_lookup[skill.name] = skill  
                
                # Add variants
                variants = SkillVariant.query.join(Skill).all()
                for variant in variants:
                    new_lookup[variant.variant_name.lower()] = variant.skill 
                    # Keep original case
                    if variant.variant_name.lower() != variant.variant_name:
                        new_lookup[variant.variant_name] = variant.skill

            # Atomic swap  
            self._skill_lookup = new_lookup

        except SQLAlchemyError as e:  
            current_app.logger.warning("Failed to build skill lookup: %s", e, exc_info=True)  
            self._skill_lookup = {}
    
    def find_skill(self, name: str) -> Optional[Skill]:
        """Find a skill by name (case-insensitive)"""
        # Try exact match first
        if not name:
            return None

        if name in self._skill_lookup:
            return self._skill_lookup[name]
        
        # Try case-insensitive
        key = name.lower()
        if key in self._skill_lookup:
            return self._skill_lookup[key]
        
        return None
    
    def refresh(self):
        """Refresh the lookup cache"""
        self._build_lookup()
    
    @property
    def lookup_dict(self) -> Dict[str, Skill]:
        """Get the current lookup dictionary"""
        return self._skill_lookup.copy()

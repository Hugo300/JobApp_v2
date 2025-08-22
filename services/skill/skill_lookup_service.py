from typing import Dict, Optional
from models import Skill, SkillVariant, db

class SkillLookupService:
    """Service for skill lookup and caching"""
    
    def __init__(self):
        self._skill_lookup: Dict[str, Skill] = {}
        self._build_lookup()
    
    def _build_lookup(self):
        """Build lookup dictionary from database"""
        try:
            self._skill_lookup = {}
            
            # Add canonical skills (active only)
            skills = Skill.query.filter_by(is_blacklisted=False).all()
            for skill in skills:
                self._skill_lookup[skill.name.lower()] = skill
                # Keep original case for exact matches
                if skill.name.lower() != skill.name:
                    self._skill_lookup[skill.name] = skill
            
            # Add variants
            variants = SkillVariant.query.join(Skill).filter(
                Skill.is_blacklisted == False
            ).all()
            for variant in variants:
                self._skill_lookup[variant.variant_name.lower()] = variant.skill
                # Keep original case
                if variant.variant_name.lower() != variant.variant_name:
                    self._skill_lookup[variant.variant_name] = variant.skill
                    
        except Exception as e:
            print(f"Warning: Failed to build skill lookup: {e}")
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
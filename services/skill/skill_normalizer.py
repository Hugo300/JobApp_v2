from typing import List

from configurations.skill_config import SkillExtractionConfig
from dtos.skill_dtos import NormalizedSkillsResult
from services.skill.skill_lookup_service import SkillLookupService
from utils.text_processing import TextProcessor

class SkillNormalizer:
    """Handles skill normalization and filtering"""
    
    def __init__(self, lookup_service: SkillLookupService, config: SkillExtractionConfig):
        self.lookup_service = lookup_service
        self.config = config
    
    def normalize_skills(self, raw_skills: List[str]) -> NormalizedSkillsResult:
        """Normalize and filter extracted skills"""
        if not raw_skills:
            return NormalizedSkillsResult(
                normalized_skills=[],
                unmatched_skills=[],
                success=True
            )
        
        try:
            normalized_skills = []
            unmatched_skills = []
            seen_skill_ids = set()
            
            for skill in raw_skills:
                # Clean and validate
                skill = skill.strip()
                if not skill:
                    continue
                
                # Check for noise
                if TextProcessor.is_noise_skill(skill, self.config.NOISE_PATTERNS, self.config.COMMON_WORDS):
                    continue
                
                # Normalize casing - preserve known patterns or use title case
                # This could be improved with a dictionary of known skill casings
                if skill.upper() in ['IOS', 'SQL', 'HTML', 'CSS', 'XML', 'JSON', 'API', 'REST', 'MYSQL', 'NOSQL']:
                    skill = skill.upper()
                elif not any(c.isupper() for c in skill[1:]):  # If not mixed case
                    skill = skill.title()
                
                # else preserve existing casing for things like "JavaScript", "TypeScript", etc.                
                # Try to match with canonical skills
                canonical_skill = self.lookup_service.find_skill(skill)
                if canonical_skill:
                    # Avoid duplicates
                    if canonical_skill.id not in seen_skill_ids:
                        normalized_skills.append(canonical_skill)
                        seen_skill_ids.add(canonical_skill.id)
                else:
                    unmatched_skills.append(skill)
            
            return NormalizedSkillsResult(
                normalized_skills=normalized_skills,
                unmatched_skills=unmatched_skills,
                success=True
            )
            
        except Exception as e:
            return NormalizedSkillsResult(
                normalized_skills=[],
                unmatched_skills=[],
                success=False,
                error=f"Normalization failed: {str(e)}"
            )
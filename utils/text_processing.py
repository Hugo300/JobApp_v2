import re
from typing import Set, List

from configurations.skill_config import SkillExtractionConfig

class TextProcessor:
    """Utilities for text cleaning and preprocessing"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and preprocess text for skill extraction"""
        if not text:
            return ""
        
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters that might interfere with extraction
        text = re.sub(r'[^\w\s\-\+\#\.\,\(\)]', ' ', text)
        
        return text
    
    @staticmethod
    def is_noise_skill(skill: str, noise_patterns: List[str], common_words: Set[str]) -> bool:
        """Check if a skill is likely noise/not a real skill"""
        skill_lower = skill.lower().strip() if skill else ""  
        if not skill_lower:  
            return True
        
        # Check minimum length
        if len(skill_lower) <= 2 and skill not in SkillExtractionConfig.ALLOWED_SHORT_SKILLS:
            return True
            
        # Check if it's just numbers
        if skill_lower.isdigit():
            return True
        
        # Check for exact matches with noise patterns
        noise_set = set(noise_patterns) 
        if skill_lower in noise_set:
            return True
        
        # Check for patterns within the skill
        for pattern in noise_patterns:
            if re.search(rf"\b{re.escape(pattern)}\b", skill_lower):  
                return True
        
        # Check for skills with too many common words
        skill_words = set(skill_lower.split())
        if len(skill_words.intersection(common_words)) > len(skill_words) / 2:
            return True
        
        return False
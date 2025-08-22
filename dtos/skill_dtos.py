from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class ExtractedSkillsResult:
    """Result from skill extraction process"""
    skills: List[str]
    total_skills: int
    success: bool
    error: Optional[str] = None

@dataclass
class NormalizedSkillsResult:
    """Result from skill normalization process"""
    normalized_skills: List['Skill']  # SQLAlchemy Skill objects
    unmatched_skills: List[str] 
    success: bool
    error: Optional[str] = None

@dataclass
class ProcessedSkillsResult:
    """Complete skill processing result"""
    extracted_skills: List[str]
    normalized_skills: List['Skill']  # SQLAlchemy Skill objects
    unmatched_skills: List[str]
    categorized_skills: Dict[str, List['Skill']]
    total_skills: int
    success: bool
    error: Optional[str] = None

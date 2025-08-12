"""
Skill matching service using the new skill extraction service
"""
import logging
from typing import List, Dict, Tuple
from .skill_extraction_service import SkillExtractionService


class SkillMatchingService:
    """Service for matching user skills against job requirements using extracted skills"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        # Use a lazy-loaded skill extractor to avoid initialization overhead
        self._skill_extractor = None

    @property
    def skill_extractor(self):
        """Lazy-load the skill extractor"""
        if self._skill_extractor is None:
            self._skill_extractor = SkillExtractionService()
        return self._skill_extractor
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize a skill for comparison"""
        return skill.lower().strip()
    
    def _calculate_similarity(self, skill1: str, skill2: str) -> float:
        """Calculate similarity between two skills"""
        skill1_norm = self._normalize_skill(skill1)
        skill2_norm = self._normalize_skill(skill2)
        
        # Exact match
        if skill1_norm == skill2_norm:
            return 1.0
        
        # Check if one skill contains the other
        if skill1_norm in skill2_norm or skill2_norm in skill1_norm:
            return 0.8
        
        # Check for common words (for compound skills like "Machine Learning")
        words1 = set(skill1_norm.split())
        words2 = set(skill2_norm.split())
        
        if words1 and words2:
            intersection = words1.intersection(words2)
            union = words1.union(words2)
            
            if intersection:
                jaccard_similarity = len(intersection) / len(union)
                if jaccard_similarity >= 0.5:  # At least 50% word overlap
                    return jaccard_similarity * 0.7  # Reduce score for partial matches
        
        return 0.0
    
    def match_skills_against_job(self, user_skills: List[str], job_extracted_skills: List[str]) -> Dict:
        """
        Match user skills against job extracted skills
        
        Args:
            user_skills: List of user skills
            job_extracted_skills: List of skills extracted from job description
            
        Returns:
            Dictionary with match analysis
        """
        if not user_skills or not job_extracted_skills:
            return {
                'match_score': 0.0,
                'matched_skills': [],
                'unmatched_user_skills': user_skills or [],
                'unmatched_job_skills': job_extracted_skills or [],
                'skill_matches': []
            }
        
        matched_skills = []
        unmatched_user_skills = []
        unmatched_job_skills = list(job_extracted_skills)
        skill_matches = []
        
        for user_skill in user_skills:
            best_match = None
            best_similarity = 0.0
            
            for job_skill in job_extracted_skills:
                similarity = self._calculate_similarity(user_skill, job_skill)
                if similarity > best_similarity and similarity >= 0.5:  # Minimum threshold
                    best_similarity = similarity
                    best_match = job_skill
            
            if best_match:
                matched_skills.append({
                    'user_skill': user_skill,
                    'job_skill': best_match,
                    'similarity': best_similarity
                })
                skill_matches.append(user_skill)
                
                # Remove matched job skill from unmatched list
                if best_match in unmatched_job_skills:
                    unmatched_job_skills.remove(best_match)
            else:
                unmatched_user_skills.append(user_skill)
        
        # Calculate match score based on user skills
        if user_skills:
            # Weight the score by similarity scores
            total_similarity = sum(match['similarity'] for match in matched_skills)
            match_score = (total_similarity / len(user_skills)) * 100
        else:
            match_score = 0.0
        
        return {
            'match_score': round(match_score, 1),
            'matched_skills': matched_skills,
            'unmatched_user_skills': unmatched_user_skills,
            'unmatched_job_skills': unmatched_job_skills,
            'skill_matches': skill_matches,
            'total_user_skills': len(user_skills),
            'total_job_skills': len(job_extracted_skills),
            'total_matches': len(matched_skills)
        }
    
    def analyze_job_match(self, job_description: str, user_skills_string: str) -> Dict:
        """
        Analyze job match using extracted skills
        
        Args:
            job_description: Job description text
            user_skills_string: Comma-separated user skills string
            
        Returns:
            Dictionary with match analysis
        """
        try:
            # Parse user skills
            if user_skills_string:
                user_skills = [skill.strip() for skill in user_skills_string.split(',') if skill.strip()]
            else:
                user_skills = []
            
            # Extract skills from job description
            if job_description and self.skill_extractor.is_available():
                job_extracted_skills = self.skill_extractor.extract_skills_simple(job_description)
            else:
                job_extracted_skills = []
            
            # Perform skill matching
            match_result = self.match_skills_against_job(user_skills, job_extracted_skills)

            # Create list of matched job skills for display purposes
            matched_job_skills = []
            for match in match_result.get('matched_skills', []):
                if 'job_skill' in match:
                    matched_job_skills.append(match['job_skill'])

            # Add legacy format for backward compatibility
            match_result['matched_keywords'] = matched_job_skills  # Job skills that matched
            match_result['unmatched_keywords'] = match_result['unmatched_user_skills']
            
            self.logger.info(f"Skill matching completed: {match_result['match_score']}% match")
            
            return match_result
            
        except Exception as e:
            self.logger.error(f"Error in skill matching analysis: {str(e)}")
            return {
                'match_score': 0.0,
                'matched_skills': [],
                'unmatched_user_skills': user_skills if 'user_skills' in locals() else [],
                'unmatched_job_skills': [],
                'skill_matches': [],
                'matched_keywords': [],  # Legacy compatibility
                'unmatched_keywords': [],  # Legacy compatibility
                'error': str(e)
            }
    
    def is_available(self) -> bool:
        """Check if skill matching service is available"""
        return self.skill_extractor.is_available()

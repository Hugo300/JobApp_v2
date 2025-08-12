"""
Refactored skill blacklist service for managing non-skill items
"""
import logging
from datetime import datetime
from typing import List, Dict, Tuple, Optional
from models import SkillBlacklist, db
from .base_service import BaseService


class SkillBlacklistService(BaseService):
    """Service for managing skill blacklists with improved error handling"""

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)

    def get_all_blacklisted_skills(self) -> List[SkillBlacklist]:
        """Get all active blacklisted skills"""
        try:
            return SkillBlacklist.get_active_blacklist()
        except Exception as e:
            self.logger.error(f"Error getting blacklisted skills: {str(e)}")
            return []

    def get_blacklisted_skill_texts(self) -> List[str]:
        """Get list of blacklisted skill texts (lowercase)"""
        try:
            blacklisted = self.get_all_blacklisted_skills()
            return [skill.skill_text.lower() for skill in blacklisted]
        except Exception as e:
            self.logger.error(f"Error getting blacklisted skill texts: {str(e)}")
            return []

    def is_blacklisted(self, skill_text: str) -> bool:
        """Check if a skill is blacklisted using model method"""
        try:
            return SkillBlacklist.is_blacklisted(skill_text)
        except Exception as e:
            self.logger.error(f"Error checking if skill is blacklisted: {str(e)}")
            return False

    def add_to_blacklist(self, skill_text: str, reason: str = None,
                        created_by: str = None) -> Tuple[bool, Optional[SkillBlacklist], str]:
        """Add a skill to the blacklist using improved model method"""
        try:
            blacklist_entry = SkillBlacklist.create(skill_text, reason, created_by)
            db.session.add(blacklist_entry)
            db.session.commit()

            self.logger.info(f"Added skill to blacklist: {skill_text}")
            return True, blacklist_entry, "Skill added to blacklist successfully"

        except ValueError as e:
            # Model validation error
            self.logger.warning(f"Validation error adding skill to blacklist: {str(e)}")
            return False, None, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error adding skill to blacklist: {str(e)}")
            return False, None, f"Error adding skill to blacklist: {str(e)}"

    def remove_from_blacklist(self, skill_id: int) -> Tuple[bool, str]:
        """Remove a skill from the blacklist (deactivate)"""
        try:
            blacklist_entry = SkillBlacklist.query.get(skill_id)
            if not blacklist_entry:
                return False, "Blacklist entry not found"

            blacklist_entry.deactivate()
            db.session.commit()

            self.logger.info(f"Removed skill from blacklist: {blacklist_entry.skill_text}")
            return True, "Skill removed from blacklist successfully"

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error removing skill from blacklist: {str(e)}")
            return False, f"Error removing skill from blacklist: {str(e)}"

    def reactivate_blacklist_entry(self, skill_id: int, reason: str = None) -> Tuple[bool, str]:
        """Reactivate a deactivated blacklist entry"""
        try:
            blacklist_entry = SkillBlacklist.query.get(skill_id)
            if not blacklist_entry:
                return False, "Blacklist entry not found"

            blacklist_entry.reactivate(reason)
            db.session.commit()

            self.logger.info(f"Reactivated blacklist entry: {blacklist_entry.skill_text}")
            return True, "Blacklist entry reactivated successfully"

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error reactivating blacklist entry: {str(e)}")
            return False, f"Error reactivating blacklist entry: {str(e)}"
    
    def filter_blacklisted_skills(self, skills: List[str]) -> Tuple[List[str], List[str]]:
        """
        Filter out blacklisted skills from a list
        Returns: (filtered_skills, blacklisted_skills_found)
        """
        try:
            if not skills:
                return [], []

            filtered_skills = []
            blacklisted_found = []

            for skill in skills:
                if not skill or not skill.strip():
                    continue

                if self.is_blacklisted(skill):
                    blacklisted_found.append(skill)
                    self.logger.debug(f"Filtered out blacklisted skill: {skill}")
                else:
                    filtered_skills.append(skill)

            return filtered_skills, blacklisted_found

        except Exception as e:
            self.logger.error(f"Error filtering blacklisted skills: {str(e)}")
            return skills, []  # Return original list if filtering fails

    def bulk_add_to_blacklist(self, skill_texts: List[str], reason: str = None,
                             created_by: str = None) -> Dict[str, any]:
        """Add multiple skills to blacklist in bulk"""
        try:
            results = {
                'added': [],
                'skipped': [],
                'errors': [],
                'total_processed': len(skill_texts)
            }

            for skill_text in skill_texts:
                try:
                    success, entry, message = self.add_to_blacklist(skill_text, reason, created_by)
                    if success:
                        results['added'].append({
                            'skill_text': skill_text,
                            'id': entry.id if entry else None
                        })
                    else:
                        results['skipped'].append({
                            'skill_text': skill_text,
                            'reason': message
                        })
                except Exception as e:
                    results['errors'].append({
                        'skill_text': skill_text,
                        'error': str(e)
                    })

            self.logger.info(f"Bulk blacklist operation: {len(results['added'])} added, "
                           f"{len(results['skipped'])} skipped, {len(results['errors'])} errors")

            return results

        except Exception as e:
            self.logger.error(f"Error in bulk blacklist operation: {str(e)}")
            return {
                'added': [],
                'skipped': [],
                'errors': [{'error': str(e)}],
                'total_processed': len(skill_texts)
            }
    
    def get_skill_suggestions_for_blacklist(self, job_id: int = None, limit: int = 50) -> List[Dict]:
        """Get suggestions for skills that might need to be blacklisted"""
        try:
            from models import JobApplication

            # Get jobs to analyze
            query = JobApplication.query
            if job_id:
                query = query.filter_by(id=job_id)

            jobs = query.all()
            if not jobs:
                return []

            skill_frequency = {}
            suspicious_skills = {}
            already_blacklisted = set(self.get_blacklisted_skill_texts())

            for job in jobs:
                extracted_skills = job.get_extracted_skills()
                for skill in extracted_skills:
                    if not skill or not skill.strip():
                        continue

                    skill_lower = skill.lower().strip()

                    # Skip if already blacklisted
                    if skill_lower in already_blacklisted:
                        continue

                    skill_frequency[skill_lower] = skill_frequency.get(skill_lower, 0) + 1

                    # Check for suspicious patterns
                    if self._is_suspicious_skill(skill):
                        if skill not in suspicious_skills:
                            suspicious_skills[skill] = {
                                'skill': skill,
                                'job_id': job.id,
                                'job_title': job.title,
                                'company': job.company,
                                'reason': self._get_suspicion_reason(skill),
                                'frequency': 0
                            }

            # Add frequency data and sort
            for skill_data in suspicious_skills.values():
                skill_lower = skill_data['skill'].lower()
                skill_data['frequency'] = skill_frequency.get(skill_lower, 1)

            # Sort by frequency (descending) and limit results
            sorted_suggestions = sorted(
                suspicious_skills.values(),
                key=lambda x: x['frequency'],
                reverse=True
            )

            return sorted_suggestions[:limit]

        except Exception as e:
            self.logger.error(f"Error getting skill suggestions: {str(e)}")
            return []

    def get_blacklist_statistics(self) -> Dict[str, any]:
        """Get statistics about the blacklist"""
        try:
            all_entries = SkillBlacklist.query.all()
            active_entries = [entry for entry in all_entries if entry.is_active]
            inactive_entries = [entry for entry in all_entries if not entry.is_active]

            # Get creation statistics
            recent_entries = [
                entry for entry in active_entries
                if entry.created_at and (datetime.utcnow() - entry.created_at).days <= 30
            ]

            return {
                'total_entries': len(all_entries),
                'active_entries': len(active_entries),
                'inactive_entries': len(inactive_entries),
                'recent_entries_30_days': len(recent_entries),
                'most_recent_entry': max(
                    (entry.created_at for entry in active_entries if entry.created_at),
                    default=None
                ),
                'oldest_entry': min(
                    (entry.created_at for entry in active_entries if entry.created_at),
                    default=None
                )
            }

        except Exception as e:
            self.logger.error(f"Error getting blacklist statistics: {str(e)}")
            return {
                'total_entries': 0,
                'active_entries': 0,
                'inactive_entries': 0,
                'recent_entries_30_days': 0,
                'most_recent_entry': None,
                'oldest_entry': None
            }
    
    def _is_suspicious_skill(self, skill: str) -> bool:
        """Check if a skill looks suspicious and might need blacklisting"""
        if not skill or not skill.strip():
            return False

        skill_lower = skill.lower().strip()

        # Skip very short skills (likely abbreviations or valid skills)
        if len(skill_lower) < 3:
            return False

        # Suspicious patterns that indicate non-skills
        suspicious_patterns = [
            'experience', 'background', 'knowledge', 'understanding', 'familiarity',
            'ability', 'skills', 'years', 'degree', 'education', 'industry',
            'related', 'relevant', 'similar', 'equivalent', 'comparable',
            'strong', 'solid', 'proven', 'demonstrated', 'excellent',
            'good', 'basic', 'advanced', 'senior', 'junior', 'entry level',
            'required', 'preferred', 'minimum', 'maximum', 'must have',
            'nice to have', 'plus', 'bonus', 'advantage'
        ]

        # Check if skill contains suspicious words
        for pattern in suspicious_patterns:
            if pattern in skill_lower:
                return True

        # Check if skill is too long (likely a phrase, not a skill)
        word_count = len(skill.split())
        if word_count > 5:
            return True

        # Check if skill contains common non-skill words
        non_skill_words = [
            'the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has',
            'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
            'may', 'might', 'can', 'must', 'shall'
        ]

        skill_words = skill_lower.split()
        non_skill_count = sum(1 for word in skill_words if word in non_skill_words)

        # If more than 30% of words are non-skill words, it's suspicious
        if word_count > 1 and (non_skill_count / word_count) > 0.3:
            return True

        # Check for numeric patterns that suggest requirements rather than skills
        import re
        if re.search(r'\d+\s*(year|month|week|day)', skill_lower):
            return True

        # Check for degree/certification patterns
        degree_patterns = [
            r'\b(bachelor|master|phd|doctorate|degree|certification|certificate)\b',
            r'\b(bs|ba|ms|ma|mba|phd)\b',
            r'\b(associate|undergraduate|graduate)\b'
        ]

        for pattern in degree_patterns:
            if re.search(pattern, skill_lower):
                return True

        return False

    def _get_suspicion_reason(self, skill: str) -> str:
        """Get reason why a skill is suspicious"""
        if not skill:
            return "Empty skill"

        skill_lower = skill.lower().strip()

        # Check for specific patterns and return appropriate reason
        if any(term in skill_lower for term in ['experience', 'background']):
            return "Contains generic experience/background terms"
        elif any(term in skill_lower for term in ['years', 'months', 'weeks']):
            return "Contains time-related terms"
        elif any(term in skill_lower for term in ['degree', 'bachelor', 'master', 'phd', 'certification']):
            return "Contains education/certification terms"
        elif any(term in skill_lower for term in ['required', 'preferred', 'must have', 'nice to have']):
            return "Contains requirement language"
        elif len(skill.split()) > 5:
            return "Too long - likely a phrase rather than a skill"
        elif any(word in skill_lower for word in ['the', 'and', 'or', 'of', 'in', 'to', 'for', 'with']):
            return "Contains common non-skill words"
        else:
            return "Pattern suggests it may not be a specific skill"

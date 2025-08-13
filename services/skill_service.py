from typing import List
import re
import spacy

from spacy.matcher import PhraseMatcher
from skillNer.skill_extractor_class import SkillExtractor
from skillNer.general_params import SKILL_DB

from models import SkillCategory, Skill, db
from utils.forms import sanitize_input
from .base_service import BaseService


# --- Singleton SpaCy Model Loading ---
# Load the spaCy model once when the module is first imported.
# This ensures it's shared across all instances of SkillService.
try:
    NLP_MODEL = spacy.load("en_core_web_lg")
    # Initialize SkillNER extractor with the pre-loaded model
    SKILL_EXTRACTOR = SkillExtractor(
        nlp=NLP_MODEL,
        skills_db=SKILL_DB,
        phraseMatcher=PhraseMatcher
    )
except OSError:
    print("SpaCy model 'en_core_web_lg' not found. Please download it using: python -m spacy download en_core_web_lg")
    NLP_MODEL = None
    SKILL_EXTRACTOR = None
# -----------------------------------


class SkillService(BaseService):
    def __init__(self):
        # Load spaCy model
        self.nlp = NLP_MODEL
        self.skill_extractor = SKILL_EXTRACTOR
        if not self.nlp or not self.skill_extractor:
            raise RuntimeError("SpaCy model or SkillNER extractor failed to load.")

    def extract_skills(self, job_description):
        """
        Extract skills from a job description using SkillNER and spaCy.

        :param job_description: str, the job description text
        :return: list of extracted skills
        """
        if not self.skill_extractor or not self.nlp:
            return {
                'skills': [],
                'error': 'Skill extraction models not available',
                'success': False
            }

        if not job_description or not job_description.strip():
            return {
                'skills': [],
                'error': 'No job description provided',
                'success': False
            }

        try:
            # Clean the text
            cleaned_text = self._clean_text(job_description)

            if not cleaned_text:
                return {
                    'skills': [],
                    'error': 'Job description is empty after cleaning',
                    'success': False
                }

            # Extract skills using SkillNER
            annotations = self.skill_extractor.annotate(cleaned_text)

            # Extract skill names from annotations
            extracted_skills = []
            if 'results' in annotations and 'full_matches' in annotations['results']:
                for match in annotations['results']['full_matches']:
                    if 'doc_node_value' in match:
                        skill_name = match['doc_node_value']
                        if skill_name and len(skill_name.strip()) > 1:  # Filter out single characters
                            extracted_skills.append(skill_name)

            # Also check for ngram matches
            if 'results' in annotations and 'ngram_scored' in annotations['results']:
                for match in annotations['results']['ngram_scored']:
                    if 'doc_node_value' in match:
                        skill_name = match['doc_node_value']
                        if skill_name and len(skill_name.strip()) > 1:
                            extracted_skills.append(skill_name)

            # Normalize and deduplicate skills
            normalized_skills = self._normalize_skills(extracted_skills)

            result = {
                'skills': normalized_skills,
                'total_skills': len(normalized_skills),
                'success': True
            }

            return result

        except Exception as e:
            return {
                'skills': [],
                'error': f'Skill extraction failed: {str(e)}',
                'success': False
            }

    def categorize_skills(self, skills):
        """
        Categorize extracted skills using the SkillCategory model.

        :param skills: list of extracted skills
        :return: dict, categorized skills
        """
        categorized_skills = {}

        # Fetch all categories and their associated skills from the database
        categories = SkillCategory.query.all()

        for category in categories:
            categorized_skills[category.name] = []
            for skill in skills['skills']:
                # Check if the skill matches any skill in the category
                if any(skill.lower() == db_skill.name.lower() for db_skill in category.skills):
                    categorized_skills[category.name].append(skill)

        return categorized_skills

    def _clean_text(self, text: str) -> str:
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
    
    def _normalize_skills(self, skills: List[str]) -> List[str]:
        """Normalize, deduplicate, and filter extracted skills"""
        if not skills:
            return []

        normalized_skills = []
        seen_skills = set()

        for skill in skills:
            # Clean the skill name
            skill = skill.strip()
            if not skill:
                continue

            # Convert to title case for consistency
            skill = skill.title()

            # Remove duplicates (case-insensitive)
            skill_lower = skill.lower()
            if skill_lower not in seen_skills:
                seen_skills.add(skill_lower)
                normalized_skills.append(skill)

        return sorted(normalized_skills)
    
    def _is_noise_skill(self, skill: str) -> bool:
        """Check if a skill is likely noise/not a real skill"""
        skill_lower = skill.lower().strip()

        # Common noise patterns
        noise_patterns = [
            # Generic phrases
            'related industry', 'relevant experience', 'similar role', 'comparable position',
            'equivalent experience', 'related field', 'similar background', 'relevant background',
            'industry experience', 'professional experience', 'work experience', 'prior experience',

            # Time-related phrases
            'years experience', 'years of experience', 'year experience', 'months experience',
            'minimum years', 'plus years', 'or more years', 'at least years',

            # Generic requirements
            'strong background', 'solid background', 'proven track record', 'demonstrated ability',
            'ability to work', 'willingness to', 'desire to', 'passion for', 'interest in',

            # Location/logistics
            'remote work', 'on site', 'hybrid work', 'flexible schedule', 'full time', 'part time',
            'contract position', 'permanent position', 'temporary position',

            # Education levels (too generic)
            'bachelor degree', 'master degree', 'phd', 'high school', 'college degree',
            'university degree', 'advanced degree',

            # Company-specific
            'company culture', 'team environment', 'fast paced', 'startup environment',
            'corporate environment', 'small team', 'large team',

            # Vague descriptors
            'good understanding', 'basic knowledge', 'working knowledge', 'familiarity with',
            'exposure to', 'some experience', 'hands on experience'
        ]

        # Check for exact matches
        if skill_lower in noise_patterns:
            return True

        # Check for patterns within the skill
        for pattern in noise_patterns:
            if pattern in skill_lower or skill_lower in pattern:
                return True

        # Check for very short skills (likely abbreviations or noise)
        if len(skill_lower) <= 2:
            return True

        # Check for skills that are just numbers
        if skill_lower.isdigit():
            return True

        # Check for skills with too many common words
        common_words = {'the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'by', 'from'}
        skill_words = set(skill_lower.split())
        if len(skill_words.intersection(common_words)) > len(skill_words) / 2:
            return True

        return False


    def get_skill_by_id(self, skill_id):
        return self.get_by_id(Skill, skill_id)
    
    def get_all_skills(self, order_by=None, include_relationships=False):
        """
        Get all skills with optimized queries

        Args:
            order_by: Order by clause
            include_relationships: Whether to eagerly load relationships

        Returns:
            List[Skill]: List of skills
        """
        try:
            query = Skill.query

            # Eagerly load relationships to prevent N+1 queries
            if include_relationships:
                from sqlalchemy.orm import joinedload
                query = query.options(
                    joinedload(Skill.skill_category)
                )

            if order_by is None:
                query = query.order_by(Skill.name.desc())
            else:
                query = query.order_by(order_by)

            return query.all()
        except Exception as e:
            return []
        
    def get_all_skills_and_category(self):
        try:
            results = db.session.query(Skill, SkillCategory).join(SkillCategory, isouter=True).filter(Skill.is_blacklisted==False).all()

            list_skills = []
            # Iterate through each tuple in the results
            for skill, category in results:
                category_name = category.name if category else ''
                category_id = category.id if category else None

                # Create a dictionary for each skill, including the category name
                skill_data = {
                    'id': skill.id,
                    'name': skill.name,
                    'category_id': category_id,
                    'category_name': category_name
                }
                list_skills.append(skill_data)
            
            return list_skills
        except Exception as e:
            return []
        
    def create_skill(self, name, category=None, is_blacklisted=False):
        """
        Create a new skill

        Args:
            name: skill name
            description: skill description

        Returns:
            tuple: (success: bool, skill: Skill, error: str)
        """
        # Validate and sanitize inputs
        try:
            if not name or not name.strip():
                return False, None, "Nname is required"

            # Sanitize all string inputs
            name = sanitize_input(name)
            category = sanitize_input(category)

        except Exception as e:
            return False, None, f"Validation error: {str(e)}"

        data = {
            'name': name,
            'category_id': category,
            'is_blacklisted': is_blacklisted
        }

        # Create the skill
        success, obj, error = self.create(Skill, **data)

        return success, obj, error
    
    def update_skill(self, skill_id, **kwargs):
        """
        Update a skill

        Args:
            skill_id: skill ID
            **kwargs: Fields to update

        Returns:
            tuple: (success: bool, skill: Skill, error: str)
        """
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            return False, None, "Skill not found"

        # Update the skill
        success, updated_skill, error = self.update(skill, **kwargs)

        return success, updated_skill, error
    
    def delete_skill(self, skill_id):
        """
        Delete a skill
        
        Args:
            skill_id: skill ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        skill = self.get_skill_by_id(skill_id)
        if not skill:
            return False, None, "skill not found"
        
        return self.delete(skill)

    def set_blacklist(self, skill_id, value):       
        return self.update_skill(skill_id, **{'is_blacklisted': value})
    
    def get_blacklist_skills(self, order_by=None):
        try:
            query = Skill.query

            # Eagerly load relationships to prevent N+1 queries
            if order_by is None:
                query = query.order_by(Skill.name.desc())
            else:
                query = query.order_by(order_by)

            return query.filter(Skill.is_blacklisted==True).all()
        except Exception as e:
            self.logger.error(f"Error getting all skills: {str(e)}")
            return []
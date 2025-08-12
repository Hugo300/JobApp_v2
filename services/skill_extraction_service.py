import spacy
import logging
import hashlib
from skillNer.skill_extractor_class import SkillExtractor
from skillNer.general_params import SKILL_DB
from spacy.matcher import PhraseMatcher
from typing import List, Dict, Optional, Tuple
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from .cache_service import cache_service, cached
from utils.skill_constants import ALL_SKILL_VARIATIONS, PROGRAMMING_PATTERNS, FRAMEWORK_PATTERNS


class SkillExtractionServiceSingleton:
    """Singleton class to ensure skill extraction models are loaded only once"""
    _instance = None
    _nlp = None
    _skill_extractor = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SkillExtractionServiceSingleton, cls).__new__(cls)
        return cls._instance

    def initialize(self, force_reinit=False):
        """Initialize the models if not already done"""
        if not self._initialized or force_reinit:
            logger = logging.getLogger(__name__)
            try:
                logger.info("Initializing spaCy and SkillNER models (one-time setup)...")
                # Load spaCy English model
                self._nlp = spacy.load("en_core_web_sm")
                logger.info("spaCy English model loaded successfully")

                # Initialize SkillNER with required parameters
                self._skill_extractor = SkillExtractor(self._nlp, SKILL_DB, PhraseMatcher)
                logger.info("SkillNER initialized successfully")

                self._initialized = True
                logger.info("Skill extraction models initialization complete")

            except Exception as e:
                logger.error(f"Error initializing skill extraction models: {str(e)}")
                self._nlp = None
                self._skill_extractor = None
                self._initialized = False
                # Re-raise the exception so calling code knows initialization failed
                raise

    @property
    def nlp(self):
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                pass  # Initialization failed, return None
        return self._nlp

    @property
    def skill_extractor(self):
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                pass  # Initialization failed, return None
        return self._skill_extractor

    def is_available(self):
        if not self._initialized:
            try:
                self.initialize()
            except Exception:
                return False  # Initialization failed
        return self._nlp is not None and self._skill_extractor is not None

    def reset_for_testing(self):
        """Reset the singleton state for testing purposes"""
        self._nlp = None
        self._skill_extractor = None
        self._initialized = False


class SkillExtractionService:
    """Service for extracting skills from job descriptions using spaCy and SkillNER"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._singleton = SkillExtractionServiceSingleton()
        self._blacklist_service = None

    @property
    def _nlp(self):
        return self._singleton.nlp

    @property
    def _skill_extractor(self):
        return self._singleton.skill_extractor

    @property
    def blacklist_service(self):
        if self._blacklist_service is None:
            from .skill_blacklist_service import SkillBlacklistService
            self._blacklist_service = SkillBlacklistService()
        return self._blacklist_service
    
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

            # Filter out noise skills
            if self._is_noise_skill(skill):
                self.logger.debug(f"Filtered out noise skill: {skill}")
                continue

            # Filter out blacklisted skills
            if self.blacklist_service.is_blacklisted(skill):
                self.logger.debug(f"Filtered out blacklisted skill: {skill}")
                continue

            # Convert to title case for consistency
            skill = skill.title()

            # Remove duplicates (case-insensitive)
            skill_lower = skill.lower()
            if skill_lower not in seen_skills:
                seen_skills.add(skill_lower)
                normalized_skills.append(skill)

        return sorted(normalized_skills)
    
    def extract_skills(self, job_description: str) -> Dict[str, List[str]]:
        """
        Extract skills from job description with caching

        Args:
            job_description: The job description text

        Returns:
            Dictionary containing extracted skills and metadata
        """
        if not self._skill_extractor or not self._nlp:
            self.logger.error("Skill extraction models not initialized")
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

            # Check cache first
            cache_key = f"skills_extraction:{hashlib.md5(cleaned_text.encode()).hexdigest()}"
            cached_result = cache_service.get(cache_key)

            if cached_result:
                self.logger.debug("Using cached skill extraction result")
                return cached_result

            # Extract skills using SkillNER
            annotations = self._skill_extractor.annotate(cleaned_text)

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

            # Cache the result for 1 hour
            cache_service.set(cache_key, result, timeout=3600)

            self.logger.info(f"Extracted {len(normalized_skills)} skills from job description")
            return result

        except Exception as e:
            self.logger.error(f"Error extracting skills: {str(e)}")
            return {
                'skills': [],
                'error': f'Skill extraction failed: {str(e)}',
                'success': False
            }
    
    def extract_skills_simple(self, job_description: str) -> List[str]:
        """
        Simple method to extract skills and return just the list
        
        Args:
            job_description: The job description text
            
        Returns:
            List of extracted skills
        """
        result = self.extract_skills(job_description)
        return result.get('skills', [])
    
    def is_available(self) -> bool:
        """Check if skill extraction service is available"""
        return self._singleton.is_available()

    def extract_skills_batch(self, job_descriptions: List[str], max_workers: int = 4) -> List[Dict[str, any]]:
        """
        Extract skills from multiple job descriptions in parallel

        Args:
            job_descriptions: List of job description texts
            max_workers: Maximum number of worker threads

        Returns:
            List of extraction results in the same order as input
        """
        if not job_descriptions:
            return []

        if not self.is_available():
            self.logger.error("Skill extraction models not available for batch processing")
            return [{'skills': [], 'error': 'Models not available', 'success': False}
                   for _ in job_descriptions]

        results = [None] * len(job_descriptions)

        # Use ThreadPoolExecutor for parallel processing
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all jobs
            future_to_index = {
                executor.submit(self.extract_skills, desc): i
                for i, desc in enumerate(job_descriptions)
            }

            # Collect results as they complete
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    result = future.result()
                    results[index] = result
                except Exception as e:
                    self.logger.error(f"Error in batch extraction for job {index}: {str(e)}")
                    results[index] = {
                        'skills': [],
                        'error': f'Extraction failed: {str(e)}',
                        'success': False
                    }

        self.logger.info(f"Completed batch skill extraction for {len(job_descriptions)} jobs")
        return results

    def extract_skills_optimized(self, job_description: str, use_cache: bool = True) -> Dict[str, any]:
        """
        Optimized skill extraction with performance improvements

        Args:
            job_description: The job description text
            use_cache: Whether to use caching (default: True)

        Returns:
            Dictionary containing extracted skills and metadata
        """
        start_time = time.time()

        if not self.is_available():
            return {
                'skills': [],
                'error': 'Skill extraction models not available',
                'success': False,
                'processing_time': 0
            }

        if not job_description or not job_description.strip():
            return {
                'skills': [],
                'error': 'No job description provided',
                'success': False,
                'processing_time': 0
            }

        try:
            # Clean the text with optimized cleaning
            cleaned_text = self._clean_text_optimized(job_description)

            if not cleaned_text:
                return {
                    'skills': [],
                    'error': 'Job description is empty after cleaning',
                    'success': False,
                    'processing_time': time.time() - start_time
                }

            # Check cache first if enabled
            cache_key = None
            if use_cache:
                cache_key = f"skills_extraction_v2:{hashlib.md5(cleaned_text.encode()).hexdigest()}"
                cached_result = cache_service.get(cache_key)

                if cached_result:
                    cached_result['processing_time'] = time.time() - start_time
                    cached_result['from_cache'] = True
                    self.logger.debug("Using cached skill extraction result")
                    return cached_result

            # Extract skills using optimized SkillNER processing
            annotations = self._skill_extractor.annotate(cleaned_text)

            # Extract and process skills with optimized logic
            extracted_skills = self._extract_skills_from_annotations(annotations)

            # Normalize and deduplicate skills with optimized processing
            normalized_skills = self._normalize_skills_optimized(extracted_skills)

            result = {
                'skills': normalized_skills,
                'total_skills': len(normalized_skills),
                'success': True,
                'processing_time': time.time() - start_time,
                'from_cache': False
            }

            # Cache the result for 2 hours if caching is enabled
            if use_cache and cache_key:
                cache_service.set(cache_key, result, timeout=7200)

            self.logger.info(f"Extracted {len(normalized_skills)} skills in {result['processing_time']:.2f}s")
            return result

        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"Error extracting skills: {str(e)} (took {processing_time:.2f}s)")
            return {
                'skills': [],
                'error': f'Skill extraction failed: {str(e)}',
                'success': False,
                'processing_time': processing_time
            }

    def _clean_text_optimized(self, text: str) -> str:
        """Optimized text cleaning with better performance"""
        if not text:
            return ""

        # Pre-compile regex patterns for better performance
        if not hasattr(self, '_compiled_patterns'):
            self._compiled_patterns = {
                'html_tags': re.compile(r'<[^>]+>'),
                'extra_whitespace': re.compile(r'\s+'),
                'special_chars': re.compile(r'[^\w\s\-\.\,\;\:\!\?]'),
                'bullet_points': re.compile(r'^[\s]*[•\-\*\+]\s*', re.MULTILINE)
            }

        # Apply cleaning operations
        text = self._compiled_patterns['html_tags'].sub(' ', text)
        text = self._compiled_patterns['bullet_points'].sub('', text)
        text = self._compiled_patterns['special_chars'].sub(' ', text)
        text = self._compiled_patterns['extra_whitespace'].sub(' ', text)

        return text.strip()

    def _extract_skills_from_annotations(self, annotations: Dict) -> List[str]:
        """Optimized skill extraction from SkillNER annotations"""
        extracted_skills = []

        # Process full matches
        if 'results' in annotations and 'full_matches' in annotations['results']:
            for match in annotations['results']['full_matches']:
                skill_name = match.get('doc_node_value')
                if skill_name and len(skill_name.strip()) > 1:
                    extracted_skills.append(skill_name)

        # Process ngram matches with score threshold
        if 'results' in annotations and 'ngram_scored' in annotations['results']:
            for match in annotations['results']['ngram_scored']:
                # Only include high-confidence matches
                if match.get('score', 0) > 0.7:  # Threshold for quality
                    skill_name = match.get('doc_node_value')
                    if skill_name and len(skill_name.strip()) > 1:
                        extracted_skills.append(skill_name)

        return extracted_skills

    def _normalize_skills_optimized(self, skills: List[str]) -> List[str]:
        """Optimized skill normalization with better performance"""
        if not skills:
            return []

        # Pre-load blacklist for batch checking
        blacklisted_skills = set(self.blacklist_service.get_blacklisted_skill_texts())

        normalized_skills = []
        seen_skills = set()

        for skill in skills:
            # Clean the skill name
            skill = skill.strip()
            if not skill or len(skill) < 2:
                continue

            # Filter out noise skills (optimized)
            if self._is_noise_skill_optimized(skill):
                continue

            # Filter out blacklisted skills (batch check)
            if skill.lower() in blacklisted_skills:
                continue

            # Convert to title case for consistency
            skill = skill.title()

            # Remove duplicates (case-insensitive)
            skill_lower = skill.lower()
            if skill_lower not in seen_skills:
                seen_skills.add(skill_lower)
                normalized_skills.append(skill)

        return sorted(normalized_skills)

    def _is_noise_skill_optimized(self, skill: str) -> bool:
        """Optimized noise skill detection"""
        if not hasattr(self, '_noise_patterns'):
            # Pre-compile noise patterns for better performance
            self._noise_patterns = [
                re.compile(r'\b\d+\s*(year|month|week|day)s?\b', re.IGNORECASE),
                re.compile(r'\b(experience|background|knowledge)\b', re.IGNORECASE),
                re.compile(r'\b(required|preferred|must|should)\b', re.IGNORECASE),
                re.compile(r'\b(good|excellent|strong|solid)\b', re.IGNORECASE)
            ]

        skill_lower = skill.lower()

        # Quick length and character checks
        if len(skill) > 50 or len(skill.split()) > 6:
            return True

        # Check against compiled patterns
        for pattern in self._noise_patterns:
            if pattern.search(skill_lower):
                return True

        return False

    def extract_skills_enhanced(self, text: str, include_soft_skills: bool = True) -> Dict[str, any]:
        """
        Enhanced skill extraction using multiple methods

        Args:
            text: Text to extract skills from
            include_soft_skills: Whether to include soft skills

        Returns:
            Dictionary with extracted skills and metadata
        """
        try:
            if not text or not text.strip():
                return {
                    'success': True,
                    'skills': [],
                    'confidence': 1.0,
                    'methods_used': []
                }

            # Method 1: Base SkillNER extraction
            base_result = self.extract_skills(text)
            all_skills = []
            methods_used = []

            if base_result.get('success', False):
                base_skills = base_result.get('skills', [])
                all_skills.extend(base_skills)
                methods_used.append('skillner')

            # Method 2: Custom dictionary matching
            dict_skills = self._extract_with_custom_dictionaries(text)
            all_skills.extend(dict_skills)
            if dict_skills:
                methods_used.append('custom_dict')

            # Method 3: Pattern-based extraction
            pattern_skills = self._extract_with_patterns(text)
            all_skills.extend(pattern_skills)
            if pattern_skills:
                methods_used.append('patterns')

            # Deduplicate and normalize
            unique_skills = list(set(all_skills))
            filtered_skills = [skill for skill in unique_skills if not self._is_noise_skill(skill)]

            # Filter soft skills if requested
            if not include_soft_skills:
                from utils.skill_constants import is_soft_skill
                filtered_skills = [skill for skill in filtered_skills if not is_soft_skill(skill)]

            return {
                'success': True,
                'skills': filtered_skills,
                'confidence': len(filtered_skills) / max(len(all_skills), 1),
                'methods_used': methods_used,
                'raw_extractions': len(all_skills),
                'unique_skills': len(filtered_skills)
            }

        except Exception as e:
            self.logger.error(f"Error in enhanced skill extraction: {str(e)}")
            return {
                'success': False,
                'skills': [],
                'error': str(e)
            }

    def _extract_with_custom_dictionaries(self, text: str) -> List[str]:
        """Extract skills using custom dictionaries"""
        extracted = []
        text_lower = text.lower()

        for main_skill, variations in ALL_SKILL_VARIATIONS.items():
            for variation in variations:
                # Use word boundaries for exact matches
                pattern = r'\b' + re.escape(variation.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    extracted.append(main_skill)
                    break  # Found one variation, don't need to check others

        return extracted

    def _extract_with_patterns(self, text: str) -> List[str]:
        """Extract skills using regex patterns"""
        extracted = []
        text_lower = text.lower()

        # Programming languages
        for pattern in PROGRAMMING_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            extracted.extend(matches)

        # Frameworks
        for pattern in FRAMEWORK_PATTERNS:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            extracted.extend(matches)

        return extracted

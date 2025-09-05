import spacy
from spacy.matcher import PhraseMatcher
from skillNer.skill_extractor_class import SkillExtractor as SkillNER
from skillNer.general_params import SKILL_DB

from configurations.skill_config import SkillExtractionConfig
from exceptions.skill_exceptions import ModelNotLoadedError
from dtos.skill_dtos import ExtractedSkillsResult
from utils.text_processing import TextProcessor

class SkillExtractor:
    """Handles NLP-based skill extraction from text"""
    
    def __init__(self, config: SkillExtractionConfig):
        self.config = config
        self.nlp = self._load_nlp_model()
        self.skill_extractor = self._load_skill_ner()
    
    def _load_nlp_model(self):
        """Load spaCy model"""
        try:
            return spacy.load(self.config.SPACY_MODEL)
        except OSError:
            raise ModelNotLoadedError(
                f"SpaCy model '{self.config.SPACY_MODEL}' not found. "
                f"Please download it using: python -m spacy download {self.config.SPACY_MODEL}"
            )
    
    def _load_skill_ner(self):
        """Load SkillNER extractor"""
        try:
            return SkillNER(self.nlp, SKILL_DB, PhraseMatcher)
        except Exception as e:
            raise ModelNotLoadedError(f"Failed to load SkillNER: {str(e)}")
        
    def _process_match_group(self, matches, extracted_skills):
        """Process a group of matches and add valid skills to the list"""
        for match in matches:
            if 'doc_node_value' in match:
                skill_name = match['doc_node_value']
                if skill_name and (
                    len(skill_name.strip()) > self.config.MIN_SKILL_LENGTH
                    or skill_name in self.config.ALLOWED_SHORT_SKILLS
                ):
                    extracted_skills.append(skill_name)
    
    def extract_skills_from_text(self, text: str) -> ExtractedSkillsResult:
        """Extract skills from text using SkillNER"""
        if not text or not text.strip():
            return ExtractedSkillsResult(
                skills=[],
                total_skills=0,
                success=False,
                error="No text provided"
            )
        
        try:
            # Clean the text
            cleaned_text = TextProcessor.clean_text(text)
            
            if not cleaned_text:
                return ExtractedSkillsResult(
                    skills=[],
                    total_skills=0,
                    success=False,
                    error="Text is empty after cleaning"
                )
            
            # Extract skills using SkillNER
            annotations = self.skill_extractor.annotate(cleaned_text)
            extracted_skills = []
            
            # Process full matches
            if 'results' in annotations and 'full_matches' in annotations['results']:
                self._process_match_group(annotations['results']['full_matches'], extracted_skills)
            
            # Process ngram matches
            if 'results' in annotations and 'ngram_scored' in annotations['results']:
                self._process_match_group(annotations['results']['ngram_scored'], extracted_skills)
            
            return ExtractedSkillsResult(
                skills=extracted_skills,
                total_skills=len(extracted_skills),
                success=True
            )
            
        except Exception as e:
            return ExtractedSkillsResult(
                skills=[],
                total_skills=0,
                success=False,
                error=f"Skill extraction failed: {str(e)}"
            )

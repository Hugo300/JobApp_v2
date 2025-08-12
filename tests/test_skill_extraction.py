"""
Tests for skill extraction functionality
"""
import pytest
from unittest.mock import Mock, patch
from services.skill_extraction_service import SkillExtractionService
from services.job_service import JobService
from models import JobApplication, db


class TestSkillExtractionService:
    """Test SkillExtractionService"""
    
    def test_clean_text(self):
        """Test text cleaning functionality"""
        service = SkillExtractionService()
        
        # Test HTML removal
        html_text = "<p>Python developer with <strong>Django</strong> experience</p>"
        cleaned = service._clean_text(html_text)
        assert "<p>" not in cleaned
        assert "<strong>" not in cleaned
        assert "Python developer with Django experience" in cleaned
        
        # Test whitespace normalization
        messy_text = "Python    developer\n\nwith   Django\texperience"
        cleaned = service._clean_text(messy_text)
        assert "Python developer with Django experience" in cleaned
    
    def test_normalize_skills(self):
        """Test skill normalization"""
        service = SkillExtractionService()
        
        skills = ["python", "PYTHON", "Python", "javascript", "JavaScript", ""]
        normalized = service._normalize_skills(skills)
        
        # Should remove duplicates and empty strings
        assert len(normalized) == 2
        assert "Python" in normalized
        assert "Javascript" in normalized
        
        # Should be sorted
        assert normalized == sorted(normalized)
    
    @patch('services.skill_extraction_service.spacy.load')
    @patch('skillNer.skill_extractor_class.SkillExtractor')
    def test_extract_skills_success(self, mock_skill_extractor_class, mock_spacy_load):
        """Test successful skill extraction"""
        # Mock spaCy model
        mock_nlp = Mock()
        mock_spacy_load.return_value = mock_nlp
        
        # Mock SkillExtractor
        mock_extractor = Mock()
        mock_skill_extractor_class.return_value = mock_extractor
        
        # Mock extraction results
        mock_extractor.annotate.return_value = {
            'results': {
                'full_matches': [
                    {'doc_node_value': 'Python'},
                    {'doc_node_value': 'Django'}
                ],
                'ngram_scored': [
                    {'doc_node_value': 'Machine Learning'}
                ]
            }
        }
        
        service = SkillExtractionService()
        result = service.extract_skills("Python developer with Django and Machine Learning experience")
        
        assert result['success'] is True
        assert len(result['skills']) == 3
        assert 'Python' in result['skills']
        assert 'Django' in result['skills']
        assert 'Machine Learning' in result['skills']
    
    @patch('services.skill_extraction_service.spacy.load')
    @patch('skillNer.skill_extractor_class.SkillExtractor')
    def test_extract_skills_empty_description(self, mock_skill_extractor_class, mock_spacy_load):
        """Test skill extraction with empty description"""
        mock_nlp = Mock()
        mock_spacy_load.return_value = mock_nlp
        mock_extractor = Mock()
        mock_skill_extractor_class.return_value = mock_extractor
        
        service = SkillExtractionService()
        result = service.extract_skills("")
        
        assert result['success'] is False
        assert result['skills'] == []
        assert 'No job description provided' in result['error']
    
    @patch('services.skill_extraction_service.spacy.load')
    def test_extract_skills_model_not_available(self, mock_spacy_load):
        """Test skill extraction when models are not available"""
        mock_spacy_load.side_effect = Exception("Model not found")

        service = SkillExtractionService()
        # Reset the singleton to force re-initialization with the mock
        service._singleton.reset_for_testing()

        result = service.extract_skills("Python developer")

        assert result['success'] is False
        assert result['skills'] == []
        assert 'Skill extraction models not available' in result['error']
    
    def test_is_available(self):
        """Test availability check"""
        service = SkillExtractionService()
        # Since models might not be available in test environment
        # we just test that the method exists and returns a boolean
        result = service.is_available()
        assert isinstance(result, bool)


class TestJobServiceSkillIntegration:
    """Test skill extraction integration in JobService"""
    
    @patch('services.job_service.SkillExtractionService')
    def test_create_job_with_skill_extraction(self, mock_skill_service_class, app):
        """Test job creation with skill extraction"""
        with app.app_context():
            # Mock skill extraction service
            mock_skill_service = Mock()
            mock_skill_service.is_available.return_value = True
            mock_skill_service.extract_skills_simple.return_value = ['Python', 'Django', 'REST API']
            mock_skill_service_class.return_value = mock_skill_service
            
            job_service = JobService()
            
            success, job, error = job_service.create_job(
                company="Test Company",
                title="Python Developer",
                description="Looking for a Python developer with Django and REST API experience"
            )
            
            assert success is True
            assert job is not None
            assert error is None
            
            # Check that skills were extracted and saved
            extracted_skills = job.get_extracted_skills()
            assert len(extracted_skills) == 3
            assert 'Python' in extracted_skills
            assert 'Django' in extracted_skills
            assert 'REST API' in extracted_skills
    
    @patch('services.job_service.SkillExtractionService')
    def test_update_job_with_skill_extraction(self, mock_skill_service_class, app):
        """Test job update with skill extraction"""
        with app.app_context():
            # Create a job first
            job = JobApplication(
                company="Test Company",
                title="Developer",
                description="Original description"
            )
            db.session.add(job)
            db.session.commit()
            
            # Mock skill extraction service
            mock_skill_service = Mock()
            mock_skill_service.is_available.return_value = True
            mock_skill_service.extract_skills_simple.return_value = ['JavaScript', 'React', 'Node.js']
            mock_skill_service_class.return_value = mock_skill_service
            
            job_service = JobService()
            
            success, updated_job, error = job_service.update_job(
                job.id,
                description="Updated description with JavaScript, React, and Node.js"
            )
            
            assert success is True
            assert updated_job is not None
            assert error is None
            
            # Check that skills were extracted and updated
            extracted_skills = updated_job.get_extracted_skills()
            assert len(extracted_skills) == 3
            assert 'JavaScript' in extracted_skills
            assert 'React' in extracted_skills
            assert 'Node.js' in extracted_skills


class TestJobApplicationSkillMethods:
    """Test JobApplication skill-related methods"""
    
    def test_get_extracted_skills_empty(self, app):
        """Test getting skills when none are set"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Developer"
            )
            
            skills = job.get_extracted_skills()
            assert skills == []
    
    def test_set_and_get_extracted_skills(self, app):
        """Test setting and getting extracted skills"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Developer"
            )
            
            test_skills = ['Python', 'Django', 'PostgreSQL']
            job.set_extracted_skills(test_skills)
            
            retrieved_skills = job.get_extracted_skills()
            assert retrieved_skills == test_skills
    
    def test_set_extracted_skills_empty(self, app):
        """Test setting empty skills list"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Developer"
            )
            
            job.set_extracted_skills([])
            assert job.extracted_skills is None
            
            skills = job.get_extracted_skills()
            assert skills == []
    
    def test_get_extracted_skills_invalid_json(self, app):
        """Test getting skills with invalid JSON"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Developer"
            )
            
            # Set invalid JSON manually
            job.extracted_skills = "invalid json"
            
            skills = job.get_extracted_skills()
            assert skills == []

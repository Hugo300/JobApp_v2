"""
Test utility functions
"""
import pytest
from unittest.mock import Mock, patch
from services.skill_matching_service import SkillMatchingService
from utils.latex import validate_latex_content


class TestSkillMatching:
    """Test skill matching service"""

    @patch('services.skill_matching_service.SkillExtractionService')
    def test_skill_matching_perfect_match(self, mock_skill_service_class):
        """Test perfect skills match using new service"""
        # Mock skill extraction service
        mock_skill_service = Mock()
        mock_skill_service.is_available.return_value = True
        mock_skill_service.extract_skills_simple.return_value = ["Python", "Flask", "JavaScript"]
        mock_skill_service_class.return_value = mock_skill_service

        skill_matcher = SkillMatchingService()
        user_skills = ["Python", "Flask", "JavaScript"]
        job_skills = ["Python", "Flask", "JavaScript"]

        result = skill_matcher.match_skills_against_job(user_skills, job_skills)

        assert result['match_score'] == 100.0
        assert len(result['matched_skills']) == 3
        assert len(result['unmatched_user_skills']) == 0

    @patch('services.skill_matching_service.SkillExtractionService')
    def test_skill_matching_partial_match(self, mock_skill_service_class):
        """Test partial skills match using new service"""
        mock_skill_service = Mock()
        mock_skill_service.is_available.return_value = True
        mock_skill_service_class.return_value = mock_skill_service

        skill_matcher = SkillMatchingService()
        user_skills = ["Python", "Flask", "JavaScript", "SQL"]
        job_skills = ["Python", "Flask"]

        result = skill_matcher.match_skills_against_job(user_skills, job_skills)

        assert result['match_score'] == 50.0  # 2 out of 4 skills matched
        assert len(result['matched_skills']) == 2
        assert len(result['unmatched_user_skills']) == 2

    @patch('services.skill_matching_service.SkillExtractionService')
    def test_skill_matching_no_match(self, mock_skill_service_class):
        """Test no skills match using new service"""
        mock_skill_service = Mock()
        mock_skill_service.is_available.return_value = True
        mock_skill_service_class.return_value = mock_skill_service

        skill_matcher = SkillMatchingService()
        user_skills = ["Python", "Flask"]
        job_skills = ["Java", "C++"]

        result = skill_matcher.match_skills_against_job(user_skills, job_skills)

        assert result['match_score'] == 0.0
        assert len(result['matched_skills']) == 0
        assert len(result['unmatched_user_skills']) == 2

    @patch('services.skill_matching_service.SkillExtractionService')
    def test_skill_matching_empty_skills(self, mock_skill_service_class):
        """Test with empty skills list"""
        mock_skill_service = Mock()
        mock_skill_service.is_available.return_value = True
        mock_skill_service_class.return_value = mock_skill_service

        skill_matcher = SkillMatchingService()
        user_skills = []
        job_skills = ["Python", "Flask"]

        result = skill_matcher.match_skills_against_job(user_skills, job_skills)

        assert result['match_score'] == 0.0
        assert len(result['matched_skills']) == 0
        assert len(result['unmatched_user_skills']) == 0

    @patch('services.skill_matching_service.SkillExtractionService')
    def test_analyze_job_match_integration(self, mock_skill_service_class):
        """Test full job match analysis"""
        mock_skill_service = Mock()
        mock_skill_service.is_available.return_value = True
        mock_skill_service.extract_skills_simple.return_value = ["Python", "Django", "PostgreSQL"]
        mock_skill_service_class.return_value = mock_skill_service

        skill_matcher = SkillMatchingService()
        job_description = "We need a Python developer with Django and PostgreSQL experience"
        user_skills = "Python, Django, JavaScript"

        result = skill_matcher.analyze_job_match(job_description, user_skills)

        assert result['match_score'] > 0
        assert 'matched_skills' in result
        assert 'skill_matches' in result
        assert 'matched_keywords' in result  # Legacy compatibility


class TestLatex:
    """Test LaTeX utilities"""
    
    def test_validate_latex_content_valid(self):
        """Test valid LaTeX content"""
        content = """
        \\documentclass{article}
        \\begin{document}
        Hello World
        \\end{document}
        """
        assert validate_latex_content(content) is True
    
    def test_validate_latex_content_invalid(self):
        """Test invalid LaTeX content"""
        content = "Just plain text without LaTeX structure"
        assert validate_latex_content(content) is False
    
    def test_validate_latex_content_empty(self):
        """Test empty LaTeX content"""
        assert validate_latex_content("") is False
        assert validate_latex_content(None) is False
        assert validate_latex_content("   ") is False
    
    def test_validate_latex_content_missing_elements(self):
        """Test LaTeX content missing required elements"""
        # Missing \\end{document}
        content = """
        \\documentclass{article}
        \\begin{document}
        Hello World
        """
        assert validate_latex_content(content) is False
        
        # Missing \\documentclass
        content = """
        \\begin{document}
        Hello World
        \\end{document}
        """
        assert validate_latex_content(content) is False

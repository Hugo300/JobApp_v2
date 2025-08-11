"""
Test utility functions
"""
import pytest
from utils.analysis import analyze_job_match, extract_keywords_from_description
from utils.latex import validate_latex_content


class TestAnalysis:
    """Test analysis utilities"""
    
    def test_analyze_job_match_perfect_match(self):
        """Test perfect skills match"""
        job_description = "We need Python, Flask, and JavaScript skills"
        skills = ["Python", "Flask", "JavaScript"]
        
        score, matched, unmatched = analyze_job_match(job_description, skills)
        
        assert score == 100.0
        assert len(matched) == 3
        assert len(unmatched) == 0
    
    def test_analyze_job_match_partial_match(self):
        """Test partial skills match"""
        job_description = "We need Python and Flask skills"
        skills = ["Python", "Flask", "JavaScript", "SQL"]
        
        score, matched, unmatched = analyze_job_match(job_description, skills)
        
        assert score == 50.0  # 2 out of 4 skills matched
        assert "python" in matched
        assert "flask" in matched
        assert "javascript" in unmatched
        assert "sql" in unmatched
    
    def test_analyze_job_match_no_match(self):
        """Test no skills match"""
        job_description = "We need Java and C++ skills"
        skills = ["Python", "Flask"]
        
        score, matched, unmatched = analyze_job_match(job_description, skills)
        
        assert score == 0.0
        assert len(matched) == 0
        assert len(unmatched) == 2
    
    def test_analyze_job_match_empty_skills(self):
        """Test with empty skills list"""
        job_description = "We need Python skills"
        skills = []
        
        score, matched, unmatched = analyze_job_match(job_description, skills)
        
        assert score == 0
        assert len(matched) == 0
        assert len(unmatched) == 0
    
    def test_analyze_job_match_empty_description(self):
        """Test with empty job description"""
        job_description = ""
        skills = ["Python", "Flask"]
        
        score, matched, unmatched = analyze_job_match(job_description, skills)
        
        assert score == 0
        assert len(matched) == 0
        assert len(unmatched) == 0
    
    def test_extract_keywords_from_description(self):
        """Test keyword extraction"""
        description = "We are looking for a Python developer with Flask experience"
        keywords = extract_keywords_from_description(description)
        
        assert isinstance(keywords, list)
        assert len(keywords) > 0
        # Should extract meaningful words, not stop words
        assert "python" in [k.lower() for k in keywords]
        assert "flask" in [k.lower() for k in keywords]
    
    def test_extract_keywords_empty_description(self):
        """Test keyword extraction with empty description"""
        keywords = extract_keywords_from_description("")
        assert keywords == []


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

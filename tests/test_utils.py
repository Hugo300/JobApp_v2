"""
Test utility functions
"""
import pytest
from unittest.mock import Mock, patch
from utils.latex import validate_latex_content


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

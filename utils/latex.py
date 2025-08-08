import os
import subprocess
import tempfile
import shutil
from pathlib import Path

def compile_latex(latex_content, filename, template_dir=None):
    """
    Compile LaTeX content to PDF, supporting section files.
    
    Args:
        latex_content: The main LaTeX content
        filename: Name for the output file
        template_dir: Directory containing template files (sections, styles, etc.)
    
    Returns:
        Path to the generated PDF file
    """
    # Create documents directory if it doesn't exist
    documents_dir = Path('documents')
    documents_dir.mkdir(exist_ok=True)
    
    # Create a temporary directory for compilation
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the main .tex file
        tex_file_path = os.path.join(temp_dir, f"{filename}.tex")
        with open(tex_file_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        # If template_dir is provided, copy all template files to temp directory
        if template_dir and os.path.exists(template_dir):
            template_path = Path(template_dir)
            if template_path.exists():
                # Copy all files from template directory to temp directory
                for item in template_path.rglob('*'):
                    if item.is_file():
                        # Calculate relative path from template directory
                        relative_path = item.relative_to(template_path)
                        target_path = Path(temp_dir) / relative_path
                        
                        # Create target directory if it doesn't exist
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Copy the file
                        shutil.copy2(item, target_path)
        
        try:
            # Run pdflatex twice to resolve references
            for run in range(2):
                result = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', temp_dir, tex_file_path],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=temp_dir  # Set working directory to temp_dir
                )
                
                # Check for compilation errors
                if result.returncode != 0:
                    error_msg = f"LaTeX compilation failed (run {run + 1}).\n"
                    error_msg += f"Output: {result.stdout}\n"
                    error_msg += f"Errors: {result.stderr}"
                    raise Exception(error_msg)
            
            # Check if PDF was generated
            pdf_file_path = os.path.join(temp_dir, f"{filename}.pdf")
            if not os.path.exists(pdf_file_path):
                raise Exception(f"PDF generation failed. LaTeX output: {result.stdout}\nErrors: {result.stderr}")
            
            # Copy the PDF to the documents directory
            final_pdf_path = documents_dir / f"{filename}.pdf"
            shutil.copy2(pdf_file_path, final_pdf_path)
            
            return str(final_pdf_path)
            
        except subprocess.TimeoutExpired:
            raise Exception("LaTeX compilation timed out")
        except FileNotFoundError:
            raise Exception("pdflatex not found. Please ensure LaTeX is installed and pdflatex is in your PATH")
        except Exception as e:
            raise Exception(f"LaTeX compilation failed: {str(e)}")

def compile_latex_template(template_path, filename, replacements=None, template_dir=None):
    """
    Compile a LaTeX template file with optional replacements.
    
    Args:
        template_path: Path to the main template file
        filename: Name for the output file
        replacements: Dictionary of placeholder replacements
        template_dir: Directory containing template files (if None, uses template_path's directory)
    
    Returns:
        Path to the generated PDF file
    """
    if not os.path.exists(template_path):
        raise Exception(f"Template file not found: {template_path}")
    
    # Read the template content
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Apply replacements if provided
    if replacements:
        for placeholder, value in replacements.items():
            content = content.replace(placeholder, str(value))
    
    # Use template directory if not specified
    if template_dir is None:
        template_dir = os.path.dirname(template_path)
    
    return compile_latex(content, filename, template_dir)

def validate_latex_content(latex_content):
    """
    Basic validation of LaTeX content.
    Returns True if content appears valid, False otherwise.
    """
    if not latex_content or not latex_content.strip():
        return False
    
    # Check for basic LaTeX structure
    required_elements = ['\\documentclass', '\\begin{document}', '\\end{document}']
    content_lower = latex_content.lower()
    
    for element in required_elements:
        if element not in content_lower:
            return False
    
    return True

def get_template_sections(template_dir):
    """
    Get a list of available section files in a template directory.
    
    Args:
        template_dir: Path to the template directory
    
    Returns:
        List of section file names (without extension)
    """
    sections = []
    if os.path.exists(template_dir):
        sections_dir = os.path.join(template_dir, 'sections')
        if os.path.exists(sections_dir):
            for file in os.listdir(sections_dir):
                if file.endswith('.tex'):
                    sections.append(file[:-4])  # Remove .tex extension
    return sections

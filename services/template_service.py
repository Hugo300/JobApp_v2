"""
Template service for handling template business logic
"""
import os
from pathlib import Path
from models import MasterTemplate, TemplateType, db
from .base_service import BaseService
from utils.latex import compile_latex_template


class TemplateService(BaseService):
    """Service for template operations"""
    
    def get_template_by_id(self, template_id):
        """Get template by ID"""
        return self.get_by_id(MasterTemplate, template_id)
    
    def get_all_templates(self, order_by=None):
        """Get all templates"""
        if order_by is None:
            order_by = MasterTemplate.name
        return self.get_all(MasterTemplate, order_by)
    
    def get_templates_by_type(self, template_type):
        """
        Get templates by type
        
        Args:
            template_type: Template type (text or file)
            
        Returns:
            List of MasterTemplate instances
        """
        return self.filter_by(MasterTemplate, template_type=template_type)
    
    def create_template(self, name, template_type, content=None, file_path=None):
        """
        Create a new template
        
        Args:
            name: Template name
            template_type: Template type (text or file)
            content: Template content (for text templates)
            file_path: File path (for file templates)
            
        Returns:
            tuple: (success: bool, template: MasterTemplate, error: str)
        """
        # Validate template type
        if template_type not in [t.value for t in TemplateType]:
            return False, None, "Invalid template type"
        
        # Validate required fields based on type
        if template_type == TemplateType.TEXT.value and not content:
            return False, None, "Content is required for text templates"
        
        if template_type == TemplateType.FILE.value and not file_path:
            return False, None, "File path is required for file templates"
        
        template_data = {
            'name': name,
            'template_type': template_type,
            'content': content,
            'file_path': file_path
        }
        
        return self.create(MasterTemplate, **template_data)
    
    def update_template(self, template_id, **kwargs):
        """
        Update a template
        
        Args:
            template_id: Template ID
            **kwargs: Fields to update
            
        Returns:
            tuple: (success: bool, template: MasterTemplate, error: str)
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return False, None, "Template not found"
        
        return self.update(template, **kwargs)
    
    def delete_template(self, template_id):
        """
        Delete a template
        
        Args:
            template_id: Template ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return False, None, "Template not found"
        
        def _delete_template():
            # If it's a file template, optionally delete the file
            if template.template_type == TemplateType.FILE.value and template.file_path:
                try:
                    file_path = Path(template.file_path)
                    if file_path.exists():
                        file_path.unlink()
                except Exception as e:
                    self.logger.warning(f"Could not delete template file {template.file_path}: {str(e)}")
            
            db.session.delete(template)
            return True
        
        return self.safe_execute(_delete_template)
    
    def compile_template(self, template_id, context_data):
        """
        Compile a template with context data
        
        Args:
            template_id: Template ID
            context_data: Dictionary of context variables
            
        Returns:
            tuple: (success: bool, compiled_content: str, error: str)
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return False, None, "Template not found"
        
        try:
            if template.template_type == TemplateType.TEXT.value:
                # Simple text template compilation
                compiled_content = template.content
                for key, value in context_data.items():
                    placeholder = f"{{{{{key}}}}}"
                    compiled_content = compiled_content.replace(placeholder, str(value))
                return True, compiled_content, None
            
            elif template.template_type == TemplateType.FILE.value:
                # File-based template compilation (LaTeX)
                if not template.file_path or not os.path.exists(template.file_path):
                    return False, None, "Template file not found"
                
                result = compile_latex_template(template.file_path, context_data)
                if result:
                    return True, result, None
                else:
                    return False, None, "Failed to compile template"
            
            else:
                return False, None, "Unknown template type"
                
        except Exception as e:
            self.logger.error(f"Error compiling template {template_id}: {str(e)}")
            return False, None, str(e)
    
    def get_template_variables(self, template_id):
        """
        Extract variables from a template
        
        Args:
            template_id: Template ID
            
        Returns:
            List of variable names found in the template
        """
        template = self.get_template_by_id(template_id)
        if not template:
            return []
        
        try:
            import re
            
            if template.template_type == TemplateType.TEXT.value:
                # Find variables in format {{variable_name}}
                variables = re.findall(r'\{\{(\w+)\}\}', template.content or '')
                return list(set(variables))
            
            elif template.template_type == TemplateType.FILE.value:
                if not template.file_path or not os.path.exists(template.file_path):
                    return []
                
                with open(template.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Find LaTeX variables in format \VAR{variable_name}
                variables = re.findall(r'\\VAR\{(\w+)\}', content)
                return list(set(variables))
            
            return []
            
        except Exception as e:
            self.logger.error(f"Error extracting variables from template {template_id}: {str(e)}")
            return []
    
    def validate_template_content(self, template_type, content=None, file_path=None):
        """
        Validate template content
        
        Args:
            template_type: Template type
            content: Template content (for text templates)
            file_path: File path (for file templates)
            
        Returns:
            tuple: (is_valid: bool, error: str)
        """
        if template_type == TemplateType.TEXT.value:
            if not content:
                return False, "Content is required for text templates"
            
            # Basic validation for text templates
            if len(content.strip()) == 0:
                return False, "Template content cannot be empty"
            
            return True, None
        
        elif template_type == TemplateType.FILE.value:
            if not file_path:
                return False, "File path is required for file templates"
            
            if not os.path.exists(file_path):
                return False, "Template file does not exist"
            
            # Check if file is readable
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(1)  # Try to read first character
                return True, None
            except Exception as e:
                return False, f"Cannot read template file: {str(e)}"
        
        return False, "Invalid template type"
    
    def duplicate_template(self, template_id, new_name):
        """
        Duplicate an existing template
        
        Args:
            template_id: Template ID to duplicate
            new_name: Name for the new template
            
        Returns:
            tuple: (success: bool, template: MasterTemplate, error: str)
        """
        original = self.get_template_by_id(template_id)
        if not original:
            return False, None, "Original template not found"
        
        return self.create_template(
            name=new_name,
            template_type=original.template_type,
            content=original.content,
            file_path=original.file_path
        )

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from app import db
from pathlib import Path
from datetime import datetime

templates_bp = Blueprint('templates', __name__)

@templates_bp.route('/', methods=['GET', 'POST'])
def templates():
    """Manage master templates"""
    from models import MasterTemplate, TemplateType
    
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        template_type = request.form.get('template_type', TemplateType.DATABASE.value)
        
        # Check if template already exists
        existing_template = MasterTemplate.query.filter_by(name=name).first()
        
        if existing_template:
            existing_template.template_type = template_type
            if template_type == TemplateType.FILE.value:
                # Create file-based template
                template_dir = Path('documents/templates_latex')
                template_dir.mkdir(parents=True, exist_ok=True)
                template_path = template_dir / f"{name}.tex"
                existing_template.file_path = str(template_path)
                existing_template.save_content(content)
            else:
                existing_template.content = content
            flash(f'Template "{name}" updated successfully!', 'success')
        else:
            if template_type == TemplateType.FILE.value:
                # Create file-based template
                template_dir = Path('documents/templates_latex')
                template_dir.mkdir(parents=True, exist_ok=True)
                template_path = template_dir / f"{name}.tex"
                new_template = MasterTemplate(
                    name=name, 
                    content=content,
                    template_type=template_type,
                    file_path=str(template_path)
                )
                new_template.save_content(content)
            else:
                new_template = MasterTemplate(name=name, content=content)
            db.session.add(new_template)
            flash(f'Template "{name}" created successfully!', 'success')
        
        db.session.commit()
        return redirect(url_for('main.templates'))
    
    templates = MasterTemplate.query.all()
    return render_template('templates.html', templates=templates)

@templates_bp.route('/<int:template_id>')
def get_template(template_id):
    """Get template content for AJAX requests"""
    from models import MasterTemplate
    template = MasterTemplate.query.get_or_404(template_id)
    return {'content': template.get_content()}

@templates_bp.route('/file/<path:template_name>')
def get_file_template(template_name):
    """Get file-based template content"""
    template_path = Path('documents/templates_latex') / f"{template_name}.tex"
    if template_path.exists():
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return {'content': content}
    else:
        return {'error': 'Template not found'}, 404

@templates_bp.route('/sections/<path:template_name>')
def get_template_sections(template_name):
    """Get available sections for a file-based template"""
    from utils.latex import get_template_sections
    template_dir = Path('documents/templates_latex') / template_name
    sections = get_template_sections(str(template_dir))
    return {'sections': sections}

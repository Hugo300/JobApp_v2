from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from app import db
from pathlib import Path
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from models import MasterTemplate, TemplateType

templates_bp = Blueprint('templates', __name__)

# Allowed file extensions for LaTeX files
ALLOWED_EXTENSIONS = {'tex', 'sty', 'cls', 'bib'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@templates_bp.route('/', methods=['GET'])
def landing():
    """Landing page showing all templates as cards"""
    templates = MasterTemplate.query.all()
    return render_template('templates_mgmt/templates_landing.html', templates=templates)

@templates_bp.route('/create', methods=['GET', 'POST'])
def create_template():    
    if request.method == 'POST':
        name = request.form['name']
        content = request.form['content']
        template_type = request.form.get('template_type', TemplateType.DATABASE.value)
        
        # Check if template already exists
        existing_template = MasterTemplate.query.filter_by(name=name).first()
        
        if existing_template:
            flash(f'Template "{name}" already exists!', 'error')
            return redirect(url_for('templates.create_template'))
        
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
            new_template = MasterTemplate(name=name, content=content, template_type=template_type)
        
        db.session.add(new_template)
        db.session.commit()
        flash(f'Template "{name}" created successfully!', 'success')
        return redirect(url_for('templates.landing'))
    
    return render_template('templates_mgmt/template_create.html')

@templates_bp.route('/<int:template_id>/view')
def view_template(template_id):
    """View a template (read-only)"""
    template = MasterTemplate.query.get_or_404(template_id)
    
    # Get the main content
    if template.template_type == TemplateType.FILE.value:
        main_content = template.get_content()
    else:
        main_content = template.content
    
    return render_template('templates_mgmt/template_view_edit.html',
                         template=template,
                         main_content=main_content,
                         read_only=True)

@templates_bp.route('/<int:template_id>/edit')
def edit_template(template_id):
    """Edit a template"""
    template = MasterTemplate.query.get_or_404(template_id)
    
    # Get the main content
    if template.template_type == TemplateType.FILE.value:
        main_content = template.get_content()
    else:
        main_content = template.content
    
    return render_template('templates_mgmt/template_view_edit.html',
                         template=template,
                         main_content=main_content,
                         read_only=False)

@templates_bp.route('/<int:template_id>/delete', methods=['DELETE'])
def delete_template(template_id):
    """Delete a template"""
    template = MasterTemplate.query.get_or_404(template_id)
    
    try:
        # If it's a file-based template, delete the files
        if template.template_type == TemplateType.FILE.value and template.file_path:
            template_path = Path(template.file_path)
            if template_path.exists():
                template_path.unlink()
            
            # Delete the sections directory if it exists
            sections_dir = template_path.parent / template.name / 'sections'
            if sections_dir.exists():
                import shutil
                shutil.rmtree(sections_dir)
        
        db.session.delete(template)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Template "{template.name}" deleted successfully'})
    except Exception as e:
        return jsonify({'error': f'Error deleting template: {str(e)}'}), 500

@templates_bp.route('/legacy', methods=['GET', 'POST'])
def templates():
    """Legacy template management page"""
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
        return redirect(url_for('templates.landing'))
    
    templates = MasterTemplate.query.all()
    return render_template('templates_mgmt/templates.html', templates=templates)

@templates_bp.route('/<int:template_id>')
def get_template(template_id):
    """Get template content for AJAX requests"""
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

@templates_bp.route('/upload_section', methods=['POST'])
def upload_section():
    """Upload a LaTeX section file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    template_name = request.form.get('template_name')
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Only .tex, .sty, .cls, .bib files are allowed'}), 400
    
    if not template_name:
        return jsonify({'error': 'Template name is required'}), 400
    
    try:
        # Create template directory if it doesn't exist
        template_dir = Path('documents/templates_latex') / template_name
        template_dir.mkdir(parents=True, exist_ok=True)
        
        # Create sections directory if it doesn't exist
        sections_dir = template_dir / 'sections'
        sections_dir.mkdir(exist_ok=True)
        
        # Save the file
        filename = secure_filename(file.filename)
        file_path = sections_dir / filename
        
        # If file already exists, add timestamp to avoid conflicts
        if file_path.exists():
            name, ext = filename.rsplit('.', 1)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{name}_{timestamp}.{ext}"
            file_path = sections_dir / filename
        
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': f'File {filename} uploaded successfully',
            'filename': filename,
            'path': str(file_path.relative_to(Path('documents/templates_latex')))
        })
    
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@templates_bp.route('/section/<path:template_name>/<path:section_name>', methods=['GET', 'POST'])
def manage_section(template_name, section_name):
    """Load or save a specific section file"""
    template_dir = Path('documents/templates_latex') / template_name
    sections_dir = template_dir / 'sections'
    section_path = sections_dir / f"{section_name}.tex"
    
    if request.method == 'GET':
        if section_path.exists():
            with open(section_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content, 'filename': f"{section_name}.tex"})
        else:
            return jsonify({'error': 'Section not found'}), 404
    
    elif request.method == 'POST':
        content = request.form.get('content', '')
        
        try:
            # Ensure directories exist
            sections_dir.mkdir(parents=True, exist_ok=True)
            
            # Save the section content
            with open(section_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({
                'success': True,
                'message': f'Section {section_name} saved successfully'
            })
        
        except Exception as e:
            return jsonify({'error': f'Save failed: {str(e)}'}), 500

@templates_bp.route('/main_file/<path:template_name>', methods=['GET', 'POST'])
def manage_main_file(template_name):
    """Load or save the main template file"""
    template_path = Path('documents/templates_latex') / f"{template_name}.tex"
    
    if request.method == 'GET':
        if template_path.exists():
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return jsonify({'content': content, 'filename': f"{template_name}.tex"})
        else:
            return jsonify({'error': 'Template file not found'}), 404
    
    elif request.method == 'POST':
        content = request.form.get('content', '')
        
        try:
            # Ensure directory exists
            template_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save the main file content
            with open(template_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            return jsonify({
                'success': True,
                'message': f'Main file {template_name}.tex saved successfully'
            })
        
        except Exception as e:
            return jsonify({'error': f'Save failed: {str(e)}'}), 500

@templates_bp.route('/list_sections/<path:template_name>')
def list_sections(template_name):
    """List all sections for a template"""
    template_dir = Path('documents/templates_latex') / template_name
    sections_dir = template_dir / 'sections'
    
    sections = []
    if sections_dir.exists():
        for file in sections_dir.iterdir():
            if file.is_file() and file.suffix == '.tex':
                sections.append({
                    'name': file.stem,
                    'filename': file.name,
                    'size': file.stat().st_size,
                    'modified': datetime.fromtimestamp(file.stat().st_mtime).isoformat()
                })
    
    return jsonify({'sections': sections})

@templates_bp.route('/delete_section/<path:template_name>/<path:section_name>', methods=['DELETE'])
def delete_section(template_name, section_name):
    """Delete a section file"""
    template_dir = Path('documents/templates_latex') / template_name
    section_path = template_dir / 'sections' / f"{section_name}.tex"
    
    if section_path.exists():
        try:
            section_path.unlink()
            return jsonify({
                'success': True,
                'message': f'Section {section_name} deleted successfully'
            })
        except Exception as e:
            return jsonify({'error': f'Delete failed: {str(e)}'}), 500
    else:
        return jsonify({'error': 'Section not found'}), 404

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from app import db
import os
from datetime import datetime

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/new', methods=['GET', 'POST'])
def new_job():
    """Create a new job application"""
    from models import JobApplication, ApplicationStatus
    if request.method == 'POST':
        company = request.form['company']
        title = request.form['title']
        description = request.form.get('description', '')
        url = request.form.get('url', '')
        
        job = JobApplication(
            company=company,
            title=title,
            description=description,
            url=url,
            status=ApplicationStatus.COLLECTED.value
        )
        
        db.session.add(job)
        db.session.commit()
        
        flash(f'Job application for {title} at {company} created successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job.id))
    
    return render_template('new_job.html')

@jobs_bp.route('/<int:job_id>')
def job_detail(job_id):
    """Show job details and allow PDF generation"""
    from models import JobApplication, UserData, MasterTemplate, ApplicationStatus
    from utils.analysis import analyze_job_match
    
    job = JobApplication.query.get_or_404(job_id)
    user_data = UserData.query.first()
    templates = MasterTemplate.query.all()
    
    # Analyze job match if user data exists
    match_score = 0
    matched_keywords = []
    unmatched_keywords = []
    
    if user_data and job.description:
        match_score, matched_keywords, unmatched_keywords = analyze_job_match(
            job.description, user_data.get_skills_list()
        )
    
    return render_template('job_detail.html', 
                         job=job, 
                         user_data=user_data,
                         templates=templates,
                         match_score=match_score,
                         matched_keywords=matched_keywords,
                         unmatched_keywords=unmatched_keywords,
                         status_options=ApplicationStatus)

@jobs_bp.route('/<int:job_id>/scrape', methods=['POST'])
def scrape_job(job_id):
    """Scrape job details from URL"""
    from models import JobApplication
    from utils.scraper import scrape_job_details
    
    job = JobApplication.query.get_or_404(job_id)
    url = request.json.get('url')
    
    if not url:
        return jsonify({'error': 'URL is required'}), 400
    
    try:
        title, company, description = scrape_job_details(url)
        
        job.title = title or job.title
        job.company = company or job.company
        job.description = description or job.description
        job.url = url
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'title': job.title,
            'company': job.company,
            'description': job.description
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/<int:job_id>/generate-pdf', methods=['POST'])
def generate_pdf(job_id):
    """Generate PDF from LaTeX content"""
    from models import JobApplication, UserData, Document, MasterTemplate, TemplateType
    from utils.latex import compile_latex, compile_latex_template
    
    job = JobApplication.query.get_or_404(job_id)
    user_data = UserData.query.first()
    
    if not user_data:
        flash('Please set up your user data first!', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    content = request.form['content']
    doc_type = request.form['type']  # CV or Cover Letter
    template_id = request.form.get('template_id')
    
    try:
        # Get template if specified
        template = None
        if template_id:
            template = MasterTemplate.query.get(template_id)
        
        # Prepare replacements
        replacements = {
            '{{NAME}}': user_data.name or '',
            '{{EMAIL}}': user_data.email or '',
            '{{PHONE}}': user_data.phone or '',
            '{{LINKEDIN}}': user_data.linkedin or '',
            '{{GITHUB}}': user_data.github or '',
            '{{COMPANY}}': job.company or '',
            '{{JOB_TITLE}}': job.title or '',
            '{{CITY}}': 'Your City',  # Default placeholder
            '{{ROLE}}': user_data.name or 'Your Role'  # Default placeholder
        }
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{job.company}_{job.title}_{doc_type}_{timestamp}".replace(' ', '_').replace('/', '_')
        
        # Compile LaTeX based on template type
        if template and template.template_type == TemplateType.FILE.value:
            # File-based template with sections
            if template.file_path and os.path.exists(template.file_path):
                template_dir = os.path.dirname(template.file_path)
                pdf_path = compile_latex_template(
                    template.file_path, 
                    filename, 
                    replacements, 
                    template_dir
                )
            else:
                raise Exception("Template file not found")
        else:
            # Database-based template or direct content
            if template:
                content = template.get_content()
            
            # Apply replacements to content
            for placeholder, value in replacements.items():
                content = content.replace(placeholder, str(value))
            
            # For file-based templates, we need to copy the template directory
            template_dir = None
            if template and template.template_type == TemplateType.FILE.value and template.file_path:
                template_dir = os.path.dirname(template.file_path)
            
            pdf_path = compile_latex(content, filename, template_dir)
        
        # Save document record
        document = Document(
            job_id=job.id,
            type=doc_type,
            file_path=pdf_path
        )
        db.session.add(document)
        db.session.commit()
        
        flash(f'{doc_type} PDF generated successfully!', 'success')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
        
    except Exception as e:
        flash(f'Error generating PDF: {str(e)}', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/<int:job_id>/download/<int:document_id>')
def download_document(job_id, document_id):
    """Download generated PDF"""
    from models import Document
    document = Document.query.get_or_404(document_id)
    
    if document.job_id != job_id:
        flash('Document not found!', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    if not os.path.exists(document.file_path):
        flash('PDF file not found!', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))
    
    return send_file(document.file_path, as_attachment=True)

@jobs_bp.route('/<int:job_id>/update-status', methods=['POST'])
def update_status(job_id):
    """Update job application status"""
    from models import JobApplication, ApplicationStatus
    job = JobApplication.query.get_or_404(job_id)
    status = request.form['status']
    
    # Validate the status
    try:
        ApplicationStatus(status)
        job.status = status
        db.session.commit()
        flash(f'Status updated to {status}', 'success')
    except ValueError:
        flash(f'Invalid status: {status}', 'error')
    
    return redirect(url_for('jobs.job_detail', job_id=job_id))

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, current_app, abort
import os
import logging
from typing import Tuple, Optional, Dict, Any
from models import JobApplication, ApplicationStatus, UserData, MasterTemplate, Document, TemplateType, JobMode, JobLog, db
from datetime import datetime
from services import JobService, UserService, LogService, TemplateService
from services.database_service import db_service, DatabaseError
from utils.latex import compile_latex, compile_latex_template
from utils.scraper import scrape_job_details
from utils.responses import success_response, error_response, flash_success, flash_error
from utils.forms import populate_job_form_choices, populate_log_form_choices, validate_job_form_data, extract_form_data, sanitize_form_data
from utils.validation import validate_job_data, ValidationError
from routes.forms import JobForm, LogForm, QuickLogForm
from markupsafe import escape

jobs_bp = Blueprint('jobs', __name__)

@jobs_bp.route('/new_job', methods=['GET', 'POST'])
def new_job():
    """Create a new job application with improved validation and error handling"""
    form = JobForm()
    job_service = JobService()

    # Populate dynamic choices
    populate_job_form_choices(form)

    if request.method == 'POST':
        if form.validate_on_submit():
            try:
                # Extract and sanitize form data
                form_fields = ['company', 'title', 'description', 'url', 'office_location', 'country', 'job_mode']
                raw_data = extract_form_data(form_fields)

                # Sanitize all form data
                sanitized_data = sanitize_form_data(raw_data)

                # Comprehensive validation using new validation utility
                is_valid, validated_data, validation_errors = validate_job_data(sanitized_data)

                if not is_valid:
                    # Display validation errors
                    for field, error_list in validation_errors.items():
                        for error in error_list:
                            flash_error(f"{field.replace('_', ' ').title()}: {error}")
                    return render_template('jobs/new_job.html', form=form)

                # Create job using service with validated data
                success, job, error = job_service.create_job(
                    company=validated_data.get('company'),
                    title=validated_data.get('title'),
                    description=validated_data.get('description'),
                    url=validated_data.get('url'),
                    office_location=validated_data.get('office_location'),
                    country=validated_data.get('country'),
                    job_mode=validated_data.get('job_mode')
                )

                if success and job:
                    current_app.logger.info(f'New job application created: {job.title} at {job.company}')
                    flash_success(f'Job application for {job.title} at {job.company} created successfully!')
                    return redirect(url_for('jobs.job_detail', job_id=job.id))
                else:
                    flash_error(f'Error creating job application: {error or "Unknown error"}')
                    current_app.logger.error(f'Error creating job application: {error}')

            except ValidationError as e:
                flash_error(f'Validation error: {str(e)}')
                current_app.logger.warning(f'Validation error in new_job: {str(e)}')
            except DatabaseError as e:
                flash_error('Database error occurred. Please try again.')
                current_app.logger.error(f'Database error in new_job: {str(e)}')
            except Exception as e:
                current_app.logger.error(f'Unexpected error in new_job: {str(e)}')
                flash_error('An unexpected error occurred. Please try again.')
        else:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash_error(f"{field.replace('_', ' ').title()}: {error}")

    return render_template('jobs/new_job.html', form=form)

@jobs_bp.route('/<int:job_id>')
def job_detail(job_id):
    """Show job details and allow PDF generation"""
    try:
        # Initialize services
        job_service = JobService()
        user_service = UserService()
        template_service = TemplateService()
        log_service = LogService()

        # Get job using service
        job = job_service.get_job_by_id(job_id)
        if not job:
            from werkzeug.exceptions import NotFound
            raise NotFound()

        user_data = user_service.get_user_data()
        templates = template_service.get_all_templates()



        # Get logs using service
        all_logs = log_service.get_logs_for_job(job_id)
        show_all = request.args.get('show_all', 'false').lower() == 'true'
        if show_all:
            recent_logs = all_logs
        else:
            recent_logs = all_logs[:10]  # Limit to 10



        return render_template('jobs/job_detail.html',
                             job=job,
                             user_data=user_data,
                             templates=templates,
                             status_options=ApplicationStatus,
                             recent_logs=recent_logs,
                             total_logs=len(all_logs))

    except Exception as e:
        current_app.logger.error(f'Error loading job detail for job {job_id}: {str(e)}')
        # If it's a 404 error, re-raise it
        if "404 Not Found" in str(e):
            from werkzeug.exceptions import NotFound
            raise NotFound()
        flash_error('An error occurred while loading the job details.')
        return redirect(url_for('main.dashboard'))

@jobs_bp.route('/scrape', methods=['POST'])
def scrape_new_job():
    """Scrape job details from URL for new job creation"""
    url = request.json.get('url')

    if not url:
        return error_response('URL is required')

    try:
        job_service = JobService()
        current_app.logger.info(f'Scraping job details from URL: {url}')

        # Use service to scrape job details
        result = job_service.scrape_job_details(url)

        if result['success']:
            current_app.logger.info(f'Scraping completed successfully')
            return success_response(result.get('message', 'Job details scraped successfully!'), {
                'title': result.get('title'),
                'company': result.get('company'),
                'description': result.get('description')
            })
        else:
            return error_response(result.get('error', 'Failed to scrape job details'))

    except Exception as e:
        current_app.logger.error(f'Error scraping job details: {str(e)}')
        return error_response('Failed to scrape job details. Please fill in the information manually.')

@jobs_bp.route('/<int:job_id>/scrape', methods=['POST'])
def scrape_job(job_id):
    """Scrape job details from URL for existing job"""
    job = db.session.get(JobApplication, job_id)
    if not job:
        abort(404)
    url = request.json.get('url')

    if not url:
        return jsonify({'error': 'URL is required'}), 400

    try:
        current_app.logger.info(f'Scraping job details from URL for job {job_id}: {url}')
        title, company, description = scrape_job_details(url)

        # Store original values for logging
        old_title = job.title
        old_company = job.company

        # Update job with scraped data (keep existing if scraping returns None)
        job.title = title or job.title
        job.company = company or job.company
        job.description = description or job.description
        job.url = url

        db.session.commit()

        # Create a log entry for the scraping action
        log_entry = JobLog(
            job_id=job_id,
            note=f'Job details updated via web scraping from {url}. Title: "{old_title}" → "{job.title}", Company: "{old_company}" → "{job.company}"'
        )
        db.session.add(log_entry)
        db.session.commit()

        current_app.logger.info(f'Job {job_id} updated via scraping - Title: {job.title}, Company: {job.company}')

        return jsonify({
            'success': True,
            'title': job.title,
            'company': job.company,
            'description': job.description,
            'message': 'Job details updated successfully using Python scraper!'
        })
    except Exception as e:
        current_app.logger.error(f'Error scraping job details for job {job_id} from {url}: {str(e)}')
        return jsonify({'error': f'Scraping failed: {str(e)}'}), 500

@jobs_bp.route('/<int:job_id>/generate-pdf', methods=['POST'])
def generate_pdf(job_id):
    """Generate PDF from LaTeX content"""

    job = db.session.get(JobApplication, job_id)
    if not job:
        abort(404)
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
            template = db.session.get(MasterTemplate, template_id)
        
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
    document = db.session.get(Document, document_id)
    if not document:
        abort(404)
    
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
    job = db.session.get(JobApplication, job_id)
    if not job:
        abort(404)
    old_status = job.status
    status = request.form['status']

    # Validate the status
    try:
        ApplicationStatus(status)
        job.status = status

        # Create a log entry for the status change
        if old_status != status:
            log_entry = JobLog(
                job_id=job_id,
                note=f'Status changed from "{old_status}" to "{status}"',
                status_change_from=old_status,
                status_change_to=status
            )
            db.session.add(log_entry)

        db.session.commit()
        flash(f'Status updated to {status}', 'success')
    except ValueError:
        flash(f'Invalid status: {status}', 'error')

    return redirect(url_for('jobs.job_detail', job_id=job_id))



@jobs_bp.route('/<int:job_id>/quick-log', methods=['POST'])
def quick_log(job_id):
    """Add a quick log entry for a job"""
    try:
        log_service = LogService()
        note = request.form.get('note', '').strip()

        if not note:
            flash_error('Log note cannot be empty.')
            return redirect(url_for('jobs.job_detail', job_id=job_id))

        if len(note) > 500:
            flash_error('Quick note cannot exceed 500 characters.')
            return redirect(url_for('jobs.job_detail', job_id=job_id))

        if len(note) < 5:
            flash_error('Quick note must be at least 5 characters long.')
            return redirect(url_for('jobs.job_detail', job_id=job_id))

        # Sanitize input
        note = escape(note)

        # Create the log entry using service
        success, log_entry, error = log_service.create_log(job_id, note)

        if success:
            current_app.logger.info(f'Quick log entry added for job {job_id}: {note[:50]}...')
            flash_success('Quick log added successfully!')
        else:
            flash_error(f'Error adding log entry: {error}')

    except Exception as e:
        current_app.logger.error(f'Error adding quick log entry for job {job_id}: {str(e)}')
        flash_error('An error occurred while adding the log entry. Please try again.')

    return redirect(url_for('jobs.job_detail', job_id=job_id))

@jobs_bp.route('/<int:job_id>/add-log', methods=['GET', 'POST'])
def add_log(job_id):
    """Add a new log entry for a job"""
    try:
        job_service = JobService()
        log_service = LogService()

        job = job_service.get_job_by_id(job_id)
        if not job:
            from werkzeug.exceptions import NotFound
            raise NotFound()

        form = LogForm()
        populate_log_form_choices(form)

        if form.validate_on_submit():
            try:
                # Sanitize input
                note = escape(form.note.data.strip())
                status_change = form.status_change.data.strip() if form.status_change.data else None

                if not note:
                    flash_error('Log note cannot be empty.')
                    return render_template('jobs/add_log.html', job=job, form=form)

                # Create the log entry using service
                success, log_entry, error = log_service.create_log(job_id, note, status_change)

                if success:
                    current_app.logger.info(f'Log entry added for job {job_id}: {note[:50]}...')
                    flash_success('Log entry added successfully!')
                    return redirect(url_for('jobs.job_detail', job_id=job_id))
                else:
                    flash_error(f'Error adding log entry: {error}')

            except Exception as e:
                current_app.logger.error(f'Error adding log entry for job {job_id}: {str(e)}')
                flash_error('An error occurred while adding the log entry. Please try again.')
        else:
            if form.errors:
                flash_error('Please correct the errors in the form.')

        return render_template('jobs/add_log.html', job=job, form=form)

    except Exception as e:
        current_app.logger.error(f'Error loading add log page for job {job_id}: {str(e)}')
        flash('An error occurred while loading the page.', 'error')
        return redirect(url_for('main.dashboard'))

@jobs_bp.route('/<int:job_id>/edit', methods=['GET', 'POST'])
def edit_job(job_id):
    """Edit an existing job application"""
    try:
        job = db.session.get(JobApplication, job_id)
        if not job:
            abort(404)
        form = JobForm()

        if request.method == 'GET':
            # Pre-populate form with existing job data
            form.company.data = job.company
            form.title.data = job.title
            form.description.data = job.description
            form.url.data = job.url
            form.office_location.data = job.office_location
            form.country.data = job.country
            form.job_mode.data = job.job_mode

        if form.validate_on_submit():
            try:
                # Sanitize inputs
                company = escape(form.company.data.strip())
                title = escape(form.title.data.strip())
                description = escape(form.description.data.strip()) if form.description.data else None
                url = form.url.data.strip() if form.url.data else None
                office_location = escape(form.office_location.data.strip()) if form.office_location.data else None
                country = escape(form.country.data.strip()) if form.country.data else None
                job_mode = form.job_mode.data.strip() if form.job_mode.data else None

                # Validate required fields
                if not company or not title:
                    flash('Company and job title are required.', 'error')
                    return render_template('jobs/edit_job.html', job=job, form=form)

                # Update job fields
                old_company = job.company
                old_title = job.title

                job.company = company
                job.title = title
                job.description = description
                job.url = url
                job.office_location = office_location
                job.country = country
                job.job_mode = job_mode

                db.session.commit()

                # Create a log entry for the edit
                log_entry = JobLog(
                    job_id=job_id,
                    note=f'Job details updated: {old_company} - {old_title} → {company} - {title}'
                )
                db.session.add(log_entry)
                db.session.commit()

                current_app.logger.info(f'Job application updated: {title} at {company}')
                flash(f'Job application for {title} at {company} updated successfully!', 'success')
                return redirect(url_for('jobs.job_detail', job_id=job_id))

            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f'Error updating job application {job_id}: {str(e)}')
                flash('An error occurred while updating the job application. Please try again.', 'error')
        else:
            if form.errors:
                flash('Please correct the errors in the form.', 'error')

        return render_template('jobs/edit_job.html', job=job, form=form)

    except Exception as e:
        current_app.logger.error(f'Error loading edit job page for job {job_id}: {str(e)}')
        flash('An error occurred while loading the page.', 'error')
        return redirect(url_for('main.dashboard'))

@jobs_bp.route('/<int:job_id>/delete', methods=['POST'])
def delete_job(job_id):
    """Delete a job application"""
    try:
        job = db.session.get(JobApplication, job_id)
        if not job:
            abort(404)

        # Store job info for logging before deletion
        job_title = job.title
        job_company = job.company

        # Delete associated documents from filesystem
        for document in job.documents:
            if document.file_path and os.path.exists(document.file_path):
                try:
                    os.remove(document.file_path)
                    current_app.logger.info(f'Deleted document file: {document.file_path}')
                except OSError as e:
                    current_app.logger.warning(f'Could not delete document file {document.file_path}: {str(e)}')

        # Delete the job (cascade will handle documents and logs)
        db.session.delete(job)
        db.session.commit()

        current_app.logger.info(f'Job application deleted: {job_title} at {job_company}')
        flash(f'Job application "{job_title}" at {job_company} has been deleted successfully.', 'success')

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting job {job_id}: {str(e)}')
        flash('An error occurred while deleting the job application. Please try again.', 'error')

    return redirect(url_for('main.dashboard'))


@jobs_bp.route('/<int:job_id>/logs/<int:log_id>/edit', methods=['GET', 'POST'])
def edit_log(job_id, log_id):
    """Edit an existing log entry"""
    try:
        job_service = JobService()
        log_service = LogService()

        job = job_service.get_job_by_id(job_id)
        if not job:
            from werkzeug.exceptions import NotFound
            raise NotFound()

        log_entry = log_service.get_log_by_id(log_id)
        if not log_entry or log_entry.job_id != job_id:
            from werkzeug.exceptions import NotFound
            raise NotFound()

        form = LogForm()
        populate_log_form_choices(form)

        if request.method == 'GET':
            # Pre-populate form with existing log data
            form.note.data = log_entry.note

        if form.validate_on_submit():
            try:
                # Sanitize input
                note = escape(form.note.data.strip())

                if not note:
                    flash_error('Log note cannot be empty.')
                    return render_template('jobs/edit_log.html', job=job, log=log_entry, form=form)

                # Update the log entry
                success, updated_log, error = log_service.update_log(log_id, note)

                if success:
                    current_app.logger.info(f'Log entry {log_id} updated for job {job_id}')
                    flash_success('Log entry updated successfully!')
                    return redirect(url_for('jobs.job_detail', job_id=job_id))
                else:
                    flash_error(f'Error updating log entry: {error}')

            except Exception as e:
                current_app.logger.error(f'Error updating log entry {log_id} for job {job_id}: {str(e)}')
                flash_error('An error occurred while updating the log entry. Please try again.')
        else:
            if form.errors:
                flash_error('Please correct the errors in the form.')

        return render_template('jobs/edit_log.html', job=job, log=log_entry, form=form)

    except Exception as e:
        current_app.logger.error(f'Error loading edit log page for log {log_id}: {str(e)}')
        flash('An error occurred while loading the page.', 'error')
        return redirect(url_for('jobs.job_detail', job_id=job_id))


@jobs_bp.route('/<int:job_id>/logs/<int:log_id>/delete', methods=['POST'])
def delete_log(job_id, log_id):
    """Delete a log entry"""
    try:
        log_service = LogService()

        log_entry = log_service.get_log_by_id(log_id)
        if not log_entry or log_entry.job_id != job_id:
            flash_error('Log entry not found.')
            return redirect(url_for('jobs.job_detail', job_id=job_id))

        # Store log info for logging before deletion
        log_note = log_entry.note[:50] + '...' if len(log_entry.note) > 50 else log_entry.note

        # Delete the log entry
        success, _, error = log_service.delete_log(log_id)

        if success:
            current_app.logger.info(f'Log entry deleted for job {job_id}: {log_note}')
            flash_success('Log entry deleted successfully!')
        else:
            flash_error(f'Error deleting log entry: {error}')

    except Exception as e:
        current_app.logger.error(f'Error deleting log entry {log_id} for job {job_id}: {str(e)}')
        flash_error('An error occurred while deleting the log entry. Please try again.')

    return redirect(url_for('jobs.job_detail', job_id=job_id))

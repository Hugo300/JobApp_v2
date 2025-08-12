from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from models import ApplicationStatus, JobMode
from services import JobService, UserService
from utils.responses import flash_success, flash_error, success_response, error_response
from utils.forms import extract_form_data, validate_user_data_form
from pathlib import Path
from markupsafe import escape

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """Dashboard showing all job applications with search and filtering"""
    try:
        job_service = JobService()

        # Get search and filter parameters
        search_query = request.args.get('search', '').strip()
        status_filter = request.args.get('status', '').strip()
        job_mode_filter = request.args.get('job_mode', '').strip()
        country_filter = request.args.get('country', '').strip()

        # Get filtered jobs using service
        jobs = job_service.filter_jobs(search_query, status_filter, job_mode_filter, country_filter)

        # Get summary statistics using service
        summary = job_service.get_job_statistics()

        # Get unique countries for filter dropdown
        countries = sorted([country for country in summary['country_counts'].keys() if country])

        return render_template('dashboard.html',
                             jobs=jobs,
                             summary=summary,
                             status_options=ApplicationStatus,
                             job_mode_options=JobMode,
                             countries=countries,
                             search_query=search_query,
                             status_filter=status_filter,
                             job_mode_filter=job_mode_filter,
                             country_filter=country_filter)

    except Exception as e:
        current_app.logger.error(f'Error loading dashboard: {str(e)}')
        flash_error('An error occurred while loading the dashboard.')
        return render_template('dashboard.html',
                             jobs=[],
                             summary={'total_jobs': 0, 'status_counts': {}, 'status_percentages': {}, 'job_mode_counts': {}, 'country_counts': {}, 'top_countries': []},
                             status_options=ApplicationStatus,
                             job_mode_options=JobMode,
                             countries=[],
                             search_query='',
                             status_filter='',
                             job_mode_filter='',
                             country_filter='')

@main_bp.route('/user', methods=['GET', 'POST'])
def user_data():
    """User profile management"""
    user_service = UserService()
    user = user_service.get_user_data()

    if request.method == 'POST':
        try:
            # Extract form data
            form_fields = ['name', 'email', 'phone', 'linkedin', 'github', 'skills']
            data = extract_form_data(form_fields)

            # Create or update user using service
            success, result, error = user_service.create_or_update_user(
                name=data['name'],
                email=data['email'],
                phone=data['phone'],
                linkedin=data['linkedin'],
                github=data['github'],
                skills=data['skills']
            )

            if success:
                flash_success('Profile updated successfully!')
                current_app.logger.info(f'User data updated for: {data["name"]}')
                return redirect(url_for('main.user_data'))
            else:
                flash_error(f'Error updating profile: {error}')
                current_app.logger.error(f'Error updating user data: {error}')

        except Exception as e:
            current_app.logger.error(f'Unexpected error in user_data: {str(e)}')
            flash_error('An unexpected error occurred.')

    return render_template('user/user_data.html', user_data=user)


@main_bp.route('/analytics')
def analytics_dashboard():
    """Job analytics dashboard"""
    try:
        from services.analytics_service import AnalyticsService
        analytics_service = AnalyticsService()

        # Get comprehensive analytics data
        analytics_data = analytics_service.get_comprehensive_analytics()

        return render_template('analytics/dashboard.html', **analytics_data)

    except Exception as e:
        current_app.logger.error(f'Error loading analytics dashboard: {str(e)}')
        flash('Error loading analytics dashboard', 'danger')
        return redirect(url_for('main.dashboard'))
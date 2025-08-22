

from flask import Blueprint, request, redirect, render_template, url_for, current_app

from services.user_service import UserService

from utils.responses import flash_success, flash_error, success_response, error_response
from utils.forms import extract_form_data, validate_user_data_form

user_bp = Blueprint('user', __name__)

@user_bp.route('/', methods=['GET', 'POST'])
def user_data():
    """User profile management"""
    user_service = UserService()
    user = user_service.get_user_data()
    user_skills = ','.join([skill.name for skill in user_service.get_user_skills(user.id)])

    if request.method == 'POST':
        try:
            # Extract form data
            form_fields = ['name', 'email', 'phone', 'linkedin', 'github', 'skills']
            data = extract_form_data(form_fields)

            # Create or update user using service
            success, _, error = user_service.create_or_update_user(
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

    return render_template('user/user_data.html', user_data=user, user_skills=user_skills)


from flask import Blueprint, request, redirect, render_template, url_for, current_app, jsonify
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from collections import defaultdict

from services.user_service import UserService
from models import UserSkill, UserData, Skill, SkillCategory, db

from utils.responses import flash_success, flash_error, success_response, error_response, flash_warning
from utils.forms import extract_form_data, validate_user_data_form

user_bp = Blueprint('user', __name__)


# Enhanced user_data route
@user_bp.route('/', methods=['GET', 'POST'])
def user_data():
    user_service = UserService()

    if request.method == 'POST':
        # Handle profile update
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        linkedin = request.form.get('linkedin')
        github = request.form.get('github')
        
        # Get or create user data
        success, user, error = user_service.create_or_update_user(
            name=name,
            email=email,
            phone=phone,
            linkedin=linkedin,
            github=github
        )

        if success:
            flash_success('Profile updated successfully!')
        else:
            flash_error(f'Failed to update profile: {error}')
        
        return redirect(url_for('user.user_data'))
    
    # GET request - display the form
    user_data = user_service.get_user_data()
    
    # Get user skills organized by category
    user_skills_by_category = {}
    if user_data:
        user_skills = db.session.query(Skill, SkillCategory).join(
            UserSkill
        ).outerjoin(
            SkillCategory, Skill.category_id == SkillCategory.id
        ).filter(
            UserSkill.user_id == user_data.id
        ).all()
        
        for skill, category in user_skills:
            category_name = category.name if category else 'Uncategorized'
            if category_name not in user_skills_by_category:
                user_skills_by_category[category_name] = []
            user_skills_by_category[category_name].append(skill)
    
    # Get all user skills for summary
    user_skills = []
    if user_data:
        user_skills = [skill for skills_list in user_skills_by_category.values() for skill in skills_list]
    
    # Get skill categories for dropdown
    skill_categories = SkillCategory.query.all()
    
    return render_template('user/user_data.html', 
                         user_data=user_data,
                         user_skills_by_category=user_skills_by_category,
                         user_skills=user_skills,
                         skill_categories=skill_categories)


@user_bp.route('/skills/add', methods=['POST'])
def add_user_skill():
    skill_name = request.form.get('skill_name', '').strip()
    category_id = request.form.get('category_id') or None
    
    if not skill_name:
        flash_error('Skill name is required!')
        return redirect(url_for('user.user_data'))
    
    # Get or create user data
    user_data = UserData.query.first()
    if not user_data:
        flash_error('Please complete your profile first!')
        return redirect(url_for('user.user_data'))
    
    # Check if skill already exists (case-insensitive)
    existing_skill = Skill.query.filter(func.lower(Skill.name) == func.lower(skill_name)).first()
    
    if not existing_skill:
        # Create new skill
        skill = Skill(name=skill_name, category_id=category_id)
        db.session.add(skill)
        db.session.flush()  # Get the ID
    else:
        skill = existing_skill
        # Update category if provided and skill doesn't have one
        if category_id and not skill.category_id:
            skill.category_id = category_id
    
    # Check if user already has this skill
    existing_user_skill = UserSkill.query.filter_by(
        user_id=user_data.id, 
        skill_id=skill.id
    ).first()
    
    if existing_user_skill:
        flash_warning(f'You already have "{skill_name}" in your skills!')
        return redirect(url_for('user.user_data'))
    
    # Add skill to user
    user_skill = UserSkill(user_id=user_data.id, skill_id=skill.id)
    db.session.add(user_skill)
    
    try:
        db.session.commit()
        flash_success(f'Successfully added "{skill_name}" to your skills!')
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception("Error adding user skill",exc_info=True)
        flash_error('Error adding skill. Please try again.')
    
    return redirect(url_for('user.user_data'))


@user_bp.route('/skills/<int:skill_id>/remove', methods=['POST'])
def remove_user_skill(skill_id):
    user_data = UserData.query.first()
    if not user_data:
        flash_error('User profile not found!')
        return redirect(url_for('user.user_data'))
    
    # Find the user skill relationship
    user_skill = UserSkill.query.filter_by(
        user_id=user_data.id, 
        skill_id=skill_id
    ).first()
    
    if not user_skill:
        flash_error('Skill not found in your profile!')
        return redirect(url_for('user.user_data'))
    
    # Get skill name for flash message
    skill = Skill.query.get(skill_id)
    skill_name = skill.name if skill else 'Unknown skill'
    
    try:
        db.session.delete(user_skill)
        db.session.commit()
        flash_success(f'Successfully removed "{skill_name}" from your skills!')
    except Exception as e:
        db.session.rollback()
        current_app.logger.exception("Error removing user skill")  
        flash_error('Error removing skill. Please try again.')
    
    return redirect(url_for('user.user_data'))
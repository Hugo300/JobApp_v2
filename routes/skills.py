from flask import Blueprint, redirect, request, jsonify, render_template, url_for, current_app
from services import SkillService, CategoryService
from models import db

skills_bp = Blueprint('skills', __name__)

# Initialize the skill extraction service
skill_extraction_service = SkillService()

@skills_bp.route('/skills_extract', methods=['POST'])
def skills_extract():
    """
    API endpoint to extract and categorize skills from a job description.

    Request JSON:
    {
        "job_description": "string"
    }

    Response JSON:
    {
        "extracted_skills": ["skill1", "skill2", ...],
        "categorized_skills": {
            "Category1": ["skill1", ...],
            "Category2": ["skill2", ...],
            ...
        }
    }
    """
    data = request.get_json()
    job_description = data.get('job_description', '')

    if not job_description:
        return jsonify({"error": "Job description is required."}), 400

    # Extract skills
    extracted_skills = skill_extraction_service.extract_skills(job_description)

    # Categorize skills
    categorized_skills = skill_extraction_service.categorize_skills(extracted_skills)    

    return jsonify({
        "extracted_skills": extracted_skills,
        "categorized_skills": categorized_skills
    }), 200



@skills_bp.route('/manage')
def skills_manage():

    skill_service = SkillService()
    skills = skill_service.get_all_skills_and_category()

    category_service = CategoryService()
    categories = category_service.get_all_categories()

    blacklist = skill_service.get_blacklist_skills()

    uncategorized_skills = skill_service.get_uncategorized_skills()

    return render_template(
        'admin/main.html',
        categories=categories,
        skills=skills,
        blacklisted_words=blacklist,
        uncategorized_skills=uncategorized_skills
    )

@skills_bp.route('/create_skill', methods=['POST'])
def skill_create():
    try:
        skill_service = SkillService()

        name = request.form.get('name')
        category = request.form.get('category_id')

        result = skill_service.create_skill(name=name, category=category, is_blacklisted=False)
        print(result)
    except Exception as e:
        print(e)
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/<int:skill_id>/edit', methods=['POST'])
def skill_update(skill_id):
    try:
        skill_service = SkillService()

        data = request.get_json()
        print(data)

        result = skill_service.update_skill(
            skill_id=skill_id,
            **{
                'name': data['name'],
                'category_id': data['category_id'],
                'is_blacklisted': False if data['is_blacklisted'] == 'False' else True
            }
        )
        print(result)
    except Exception as e:
        print(e)
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/<int:skill_id>/delete', methods=['POST'])
def skill_delete(skill_id):
    try:
        skill_service = SkillService()
        skill_service.delete_skill(skill_id=skill_id)
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))



@skills_bp.route('/create_blacklist', methods=['POST'])
def blacklist_create():
    try:
        skill_service = SkillService()

        name = request.form.get('name')
        category = request.form.get('category_id')

        result = skill_service.create_skill(name=name, category=category, is_blacklisted=True)
        print(result)
    except Exception as e:
        print(e)
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/<int:skill_id>/add_blacklist', methods=['POST'])
def skill_add_blacklist(skill_id):
    try:
        skill_service = SkillService()
        skill_service.set_blacklist(skill_id=skill_id, value=True)
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/<int:skill_id>/remove_blacklist', methods=['POST'])
def skill_remove_blacklist(skill_id):
    try:
        skill_service = SkillService()
        skill_service.set_blacklist(skill_id=skill_id, value=False)
    except Exception as e:
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))


@skills_bp.route('/create_category', methods=['POST'])
def category_create():
    try:
        service = CategoryService()

        name = request.form.get('name')
        description = request.form.get('description')

        result = service.create_category(name=name, description=description)
        print(result)
    except Exception as e:
        print(e)
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/category/<int:category_id>/delete', methods=['POST'])
def category_delete(category_id):
    try:
        current_app.logger.info('category_delete route called')
        current_app.logger.info(f'Category ID: {category_id}')

        service = CategoryService()
        success, result, error = service.delete_category(category_id)

        if success:
            current_app.logger.info('Category deleted successfully')
        else:
            current_app.logger.error(f'Failed to delete category: {error}')

    except Exception as e:
        current_app.logger.error(f'Error in category_delete: {e}')
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))

@skills_bp.route('/category/<int:category_id>/edit', methods=['POST'])
def category_update(category_id):
    try:
        service = CategoryService()

        data = request.get_json()
        print(data)

        result = service.update_category(
            category_id=category_id,
            **{
                'name': data['name'],
                'description': data['description']
            }
        )
        print(result)
    except Exception as e:
        print(e)
        db.session.rollback()

    return redirect(url_for('skills.skills_manage'))




@skills_bp.route('/test', methods=['GET'])
def test_page():
    """
    Render a test page for the skills API.
    """
    from flask_wtf.csrf import generate_csrf
    csrf_token = generate_csrf()
    return render_template('test_skills.html', csrf_token=csrf_token)

@skills_bp.route('/uncategorized_skills', methods=['GET'])
def uncategorized_skills():
    """
    Fetch skills with no category and not blacklisted.
    """
    skill_service = SkillService()
    uncategorized_skills = skill_service.get_uncategorized_skills()

    return render_template(
        'admin/uncategorized_skills.html',
        uncategorized_skills=uncategorized_skills
    )

@skills_bp.route('/mass_edit_skills', methods=['POST'])
def mass_edit_skills():
    """
    Endpoint to handle mass editing of skills.
    """
    try:
        skill_ids = request.form.getlist('skill_ids')
        new_category_id = request.form.get('new_category_id')

        if not skill_ids:
            return jsonify({"error": "No skills selected for editing."}), 400

        skill_service = SkillService()
        for skill_id in skill_ids:
            skill_service.update_skill(skill_id, category_id=new_category_id)

        return redirect(url_for('skills.uncategorized_skills'))
    except Exception as e:
        print(f"Error during mass edit: {e}")
        return jsonify({"error": "An error occurred during mass editing."}), 500

from flask import Blueprint, redirect, request, jsonify, render_template, url_for
from services import SkillService, CategoryService
from models import db

skills_bp = Blueprint('skills', __name__)

# Initialize the skill extraction service
skill_extraction_service = SkillService()

@skills_bp.route('/extract_skills', methods=['POST'])
def extract_skills():
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

    # # Extract skills
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

    return render_template(
        'admin/skills.html',
        categories=categories,
        skills=skills,
        blacklisted_words=blacklist
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

@skills_bp.route('/<int:category_id>/delete', methods=['POST'])
def category_delete(category_id):
    print('hello')
    print(category_id)
    return redirect(url_for('skills.skills_manage'))






@skills_bp.route('/test', methods=['GET'])
def test_page():
    """
    Render a test page for the skills API.
    """
    from flask_wtf.csrf import generate_csrf
    csrf_token = generate_csrf()
    return render_template('test_skills.html', csrf_token=csrf_token)

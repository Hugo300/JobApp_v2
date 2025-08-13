from flask import Blueprint, request, jsonify, render_template
from services.skill_service import SkillService

from utils.json import make_serializable

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


@skills_bp.route('/test', methods=['GET'])
def test_page():
    """
    Render a test page for the skills API.
    """
    from flask_wtf.csrf import generate_csrf
    csrf_token = generate_csrf()
    return render_template('test_skills.html', csrf_token=csrf_token)

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from models import Skill, SkillVariant, SkillCategory, db
from services.skill.skill_service import get_skill_service

skill_bp = Blueprint('skill', __name__)


@skill_bp.route('')
def manage_skills():
    """Manage skills with blacklist filtering"""
    # Get blacklist filter parameter, default to 'active' (non-blacklisted)
    blacklist_filter = request.args.get('blacklist', 'active')
    # Get the skill service instance
    skill_service = get_skill_service()
    
    try:
        # Use SkillService to get skills based on filter
        if blacklist_filter == 'active':
            skills = skill_service.get_all_active_skills(include_relationships=True)
        elif blacklist_filter == 'blacklisted':
            skills = skill_service.get_blacklist_skills()
        else:  # 'all'
            skills = skill_service.get_all_skills(include_relationships=True)

        # Calculate total variants count
        total_variants = sum(len(skill.variants) for skill in skills)

        # Get categories for the filter dropdown   
        categories = SkillCategory.query.all()

        return render_template('admin/skill/skill_manage.html',
                               skills=skills, 
                               total_variants=total_variants,
                               categories=categories,
                               current_blacklist_filter=blacklist_filter)
                               
    except Exception as e:
        flash(f'Error loading skills: {str(e)}', 'error')
        return render_template('admin/skill/skill_manage.html',
                               skills=[], 
                               total_variants=0,
                               categories=[],
                               current_blacklist_filter=blacklist_filter)

@skill_bp.route('/<int:skill_id>/toggle-blacklist', methods=['POST'])
def toggle_blacklist(skill_id):
    """Toggle blacklist status of a skill"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        # Get the current skill
        skill = skill_service.get_skill_by_id(skill_id)
        if not skill:
            flash('Skill not found', 'error')
            return redirect(url_for('skill.manage_skills'))
        
        # Toggle blacklist status using SkillService
        new_status = not skill.is_blacklisted
        success, updated_skill, error = skill_service.set_blacklist(skill_id, new_status)
        
        if success:
            action = "blacklisted" if new_status else "removed from blacklist"
            flash(f'Skill "{updated_skill.name}" has been {action}', 'success')
        else:
            flash(f'Error updating skill: {error}', 'error')
        
    except Exception as e:
        flash(f'Error toggling blacklist: {str(e)}', 'error')
    
    # Redirect back to the same page with current filters
    blacklist_filter = request.form.get('current_filter', 'active')
    return redirect(url_for('skill.manage_skills', blacklist=blacklist_filter))

@skill_bp.route('/<int:skill_id>/variants/add', methods=['POST'])
def add_variant(skill_id):
    """Add a new variant to a skill"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        # Verify skill exists using SkillService
        skill = skill_service.get_skill_by_id(skill_id)
        if not skill:
            flash('Skill not found', 'error')
            return redirect(url_for('skill.manage_skills'))
        
        variant_name = request.form.get('variant_name', '').strip()
        
        if not variant_name:
            flash('Variant name cannot be empty', 'error')
            return redirect(url_for('skill.edit_skill', skill_id=skill_id))
        
        if len(variant_name) > 255:  
            flash('Variant name must be 255 characters or less', 'error')  
            return redirect(url_for('skill.edit_skill', skill_id=skill_id))
        
        # Check if variant exists as a main skill name using SkillService
        if skill_service.get_skill_by_name(variant_name):
            flash('This variant name conflicts with an existing skill', 'error')
            return redirect(url_for('skill.edit_skill', skill_id=skill_id))

        # Check if variant already exists for this skill
        try:
            variant = SkillVariant(skill_id=skill_id, variant_name=variant_name)
            db.session.add(variant)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash('This variant already exists', 'error')
            return redirect(url_for('skill.edit_skill', skill_id=skill_id))
        
        # Refresh the skill service cache since we added a variant
        skill_service.refresh_cache()
        
        flash(f'Variant "{variant_name}" added successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding variant: {str(e)}', 'error')
    
    return redirect(url_for('skill.edit_skill', skill_id=skill_id))

@skill_bp.route('/variants/<int:variant_id>/delete', methods=['POST'])
def delete_variant(variant_id):
    """Delete a skill variant"""
    skill_id = None

    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        variant = SkillVariant.query.get_or_404(variant_id)
        skill_id = variant.skill_id
        variant_name = variant.variant_name
        
        db.session.delete(variant)
        db.session.commit()
        
        # Refresh the skill service cache since we deleted a variant
        skill_service.refresh_cache()
        
        flash(f'Variant "{variant_name}" deleted successfully', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting variant: {str(e)}', 'error')

        if not skill_id:
            return redirect(url_for('skill.manage_skills'))
    
    return redirect(url_for('skill.edit_skill', skill_id=skill_id))

@skill_bp.route('/create', methods=['GET', 'POST'])
def create_skill():
    """Create a new skill"""
    if request.method == 'GET':
        categories = SkillCategory.query.all()
        return render_template('admin/skill/skill_create.html', categories=categories)
    
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id')
        is_blacklisted = bool(request.form.get('is_blacklisted'))
        
        if category_id:
            category_id = int(category_id)
        else:
            category_id = None
        
        success, skill, error = skill_service.create_skill(
            name=name,
            category=category_id,
            is_blacklisted=is_blacklisted
        )
        
        if success:
            flash(f'Skill "{skill.name}" created successfully', 'success')
            return redirect(url_for('skill.manage_skills'))
        else:
            flash(f'Error creating skill: {error}', 'error')
            
    except Exception as e:
        flash(f'Error creating skill: {str(e)}', 'error')
    
    # Reload form with categories on error
    categories = SkillCategory.query.all()
    return render_template('admin/skill/skill_create.html', categories=categories)
# Utility functions for skill extraction/matching

@skill_bp.route('/<int:skill_id>/edit', methods=['GET', 'POST'])
def edit_skill(skill_id):
    """Edit an existing skill - comprehensive edit page"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        skill = skill_service.get_skill_by_id(skill_id)
        if not skill:
            flash('Skill not found', 'error')
            return redirect(url_for('skill.manage_skills'))
        
        if request.method == 'GET':
            # Load skill with all relationships for the edit page
            skill = skill_service.get_skill_by_id(skill_id, include_relationships=True)
            categories = SkillCategory.query.all()
            return render_template('admin/skill/skill_edit.html', 
                                 skill=skill, 
                                 categories=categories)
        
        # Handle POST request
        name = request.form.get('name', '').strip()
        category_id = request.form.get('category_id')
        is_blacklisted = bool(request.form.get('is_blacklisted'))
        
        if category_id:
            category_id = int(category_id)
        else:
            category_id = None
        
        success, updated_skill, error = skill_service.update_skill(
            skill_id,
            name=name,
            category_id=category_id,
            is_blacklisted=is_blacklisted
        )
        
        if success:
            flash(f'Skill "{updated_skill.name}" updated successfully', 'success')
            # Stay on the edit page to continue editing
            return redirect(url_for('skill.edit_skill', skill_id=skill_id))
        else:
            flash(f'Error updating skill: {error}', 'error')
            
    except Exception as e:
        flash(f'Error editing skill: {str(e)}', 'error')
        return redirect(url_for('skill.manage_skills'))

@skill_bp.route('/<int:skill_id>/delete', methods=['POST'])
def delete_skill(skill_id):
    """Delete a skill"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        skill = skill_service.get_skill_by_id(skill_id)
        if not skill:
            flash('Skill not found', 'error')
            return redirect(url_for('skill.manage_skills'))
        
        skill_name = skill.name
        success, deleted, error = skill_service.delete_skill(skill_id)
        
        if success:
            flash(f'Skill "{skill_name}" deleted successfully', 'success')
        else:
            flash(f'Error deleting skill: {error}', 'error')
            
    except Exception as e:
        flash(f'Error deleting skill: {str(e)}', 'error')
    
    return redirect(url_for('skill.manage_skills'))


# API endpoints for AJAX functionality
@skill_bp.route('/api/skills/<int:skill_id>/variants')
def api_get_variants(skill_id):
    """Get variants for a skill via API"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        skill = skill_service.get_skill_by_id(skill_id, include_relationships=True)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        
        variants = [{'id': v.id, 'name': v.variant_name} for v in skill.variants]
        return jsonify(variants)
        
    except Exception as e:
        current_app.logger.exception("api_get_variants failed")
        return jsonify({'error': str(e)}), 500

@skill_bp.route('/api/skills/search')
def api_search_skills():
    """Search skills via API"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        query = request.args.get('q', '').strip()

        # validate query length and content
        if len(query) > 100:
            return jsonify({'error': 'Query too long'}), 400
        if not query:
            return jsonify([])

        # Query database directly with limit
        query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        matching_skills = Skill.query.filter(
            Skill.name.ilike(f'%{query}%')
        ).options(joinedload(Skill.category)).limit(10).all()
        
        results = [{
            'id': s.id, 
            'name': s.name, 
            'category': s.category.name if s.category else None
        } for s in matching_skills]
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.exception("api_search_skills failed")
        return jsonify({'error': str(e)}), 500

@skill_bp.route('/api/skills/extract', methods=['POST'])
def api_extract_skills():
    """Extract skills from text via API"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()

        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'No text provided'}), 400
        
        text = data['text']
        result = skill_service.process_job_description(text)
        
        if result.success:
            return jsonify({
                'success': True,
                'extracted_skills': result.extracted_skills,
                'normalized_skills': [{'id': s.id, 'name': s.name} for s in result.normalized_skills],
                'unmatched_skills': result.unmatched_skills,
                'categorized_skills': {
                    category: [{'id': s.id, 'name': s.name} for s in skills]
                    for category, skills in result.categorized_skills.items()
                },
                'total_skills': result.total_skills
            })
        else:
            return jsonify({
                'success': False,
                'error': result.error
            }), 400
            
    except Exception as e:
        current_app.logger.exception("api_extract_skills failed")
        return jsonify({'error': str(e)}), 500

@skill_bp.route('/api/skills/audit', methods=['POST'])
def api_audit_skills():
    """Audit existing job skills via API"""
    try:
        # Get the skill service instance
        skill_service = get_skill_service()
        
        audit_result = skill_service.audit_existing_job_skills()
        return jsonify(audit_result)
        
    except Exception as e:
        current_app.logger.exception("api_sufit_skills failed")
        return jsonify({'error': str(e)}), 500

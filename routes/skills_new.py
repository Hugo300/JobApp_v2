from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from sqlalchemy.orm import joinedload

from models import Skill, SkillVariant, SkillCategory, db

skill_new_bp = Blueprint('skill', __name__)

@skill_new_bp.route('')
def manage_skills():
    # Get blacklist filter parameter, default to 'active' (non-blacklisted)
    blacklist_filter = request.args.get('blacklist', 'active')
    
    # Build query with eager loading
    query = Skill.query.options(joinedload(Skill.category))
    
    # Apply blacklist filter
    if blacklist_filter == 'active':
        query = query.filter(Skill.is_blacklisted == False)
    elif blacklist_filter == 'blacklisted':
        query = query.filter(Skill.is_blacklisted == True)

    # run query
    skills = query.all()

    # Calculate total variants count
    total_variants = sum(len(skill.variants) for skill in skills)

    # Get categories for the filter dropdown   
    categories = SkillCategory.query.all()

    return render_template('admin/skills_new.html',
                           skills=skills, 
                           total_variants=total_variants,
                           categories=categories,
                           current_blacklist_filter=blacklist_filter)

@skill_new_bp.route('/<int:skill_id>/toggle-blacklist', methods=['POST'])
def toggle_blacklist(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    
    # Toggle blacklist status
    skill.is_blacklisted = not skill.is_blacklisted
    db.session.commit()
    
    action = "blacklisted" if skill.is_blacklisted else "removed from blacklist"
    flash(f'Skill "{skill.name}" has been {action}', 'success')
    
    # Redirect back to the same page with current filters
    blacklist_filter = request.form.get('current_filter', 'active')
    return redirect(url_for('skill.manage_skills', blacklist=blacklist_filter))

@skill_new_bp.route('/<int:skill_id>/variants')
def manage_variants(skill_id):
    skill = Skill.query.options(joinedload(Skill.category)).get_or_404(skill_id)
    return render_template('admin/skill_variants.html', skill=skill)

@skill_new_bp.route('/<int:skill_id>/variants/add', methods=['POST'])
def add_variant(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    variant_name = request.form.get('variant_name', '').strip()
    
    if not variant_name:
        flash('Variant name cannot be empty', 'error')
        return redirect(url_for('skill.manage_variants', skill_id=skill_id))
    
    # Check if variant already exists for this skill
    existing = SkillVariant.query.filter_by(skill_id=skill_id, variant_name=variant_name).first()
    if existing:
        flash('This variant already exists', 'error')
        return redirect(url_for('skill.manage_variants', skill_id=skill_id))
    
    # Check if variant exists as a main skill name
    if Skill.query.filter_by(name=variant_name).first():
        flash('This variant name conflicts with an existing skill', 'error')
        return redirect(url_for('skill.manage_variants', skill_id=skill_id))
    
    variant = SkillVariant(skill_id=skill_id, variant_name=variant_name)
    db.session.add(variant)
    db.session.commit()
    
    flash(f'Variant "{variant_name}" added successfully', 'success')
    return redirect(url_for('skill.manage_variants', skill_id=skill_id))

@skill_new_bp.route('/variants/<int:variant_id>/delete', methods=['POST'])
def delete_variant(variant_id):
    variant = SkillVariant.query.get_or_404(variant_id)
    skill_id = variant.skill_id
    
    db.session.delete(variant)
    db.session.commit()
    
    flash('Variant deleted successfully', 'success')
    return redirect(url_for('skill.manage_variants', skill_id=skill_id))

# Utility functions for skill extraction/matching

def find_canonical_skill(extracted_skill_name):
    """
    Find the canonical skill for a given extracted skill name.
    Returns the Skills object if found, None otherwise.
    """
    # First check if it's a main skill
    skill = Skill.query.filter_by(name=extracted_skill_name).first()
    if skill:
        return skill
    
    # Then check if it's a variant
    variant = SkillVariant.query.filter_by(variant_name=extracted_skill_name).first()
    if variant:
        return variant.skill
    
    # Try case-insensitive search
    skill = Skill.query.filter(Skill.name.ilike(extracted_skill_name)).first()
    if skill:
        return skill
    
    variant = SkillVariant.query.filter(SkillVariant.variant_name.ilike(extracted_skill_name)).first()
    if variant:
        return variant.skill
    
    return None

def get_all_skill_names():
    """
    Get all possible skill names (canonical + variants) for extraction.
    Useful for creating lookup dictionaries.
    """
    names = {}
    
    # Add canonical skills
    for skill in Skill.query.all():
        names[skill.name.lower()] = skill
        names[skill.name] = skill  # Keep original case too
    
    # Add variants
    for variant in SkillVariant.query.all():
        names[variant.variant_name.lower()] = variant.skill
        names[variant.variant_name] = variant.skill  # Keep original case too
    
    return names

# API endpoints for AJAX functionality
@skill_new_bp.route('/api/skills/<int:skill_id>/variants')
def api_get_variants(skill_id):
    skill = Skill.query.get_or_404(skill_id)
    variants = [{'id': v.id, 'name': v.variant_name} for v in skill.variants]
    return jsonify(variants)

@skill_new_bp.route('/api/skills/search')
def api_search_skills():
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    skills = Skill.query.filter(Skill.name.ilike(f'%{query}%')).limit(10).all()
    results = [{'id': s.id, 'name': s.name, 'category': s.category} for s in skills]
    return jsonify(results)
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, jsonify
from services.skill.category_service import get_category_service
from utils.responses import flash_success

skill_category_bp = Blueprint('skill_category', __name__)

# Get the category service instance
category_service = get_category_service()

@skill_category_bp.route('')
def manage_categories():
    """Manage skill categories with skill counts"""
    try:
        # Get all categories with counts
        categories = category_service.get_all_categories(include_counts=True)
        
        # Get statistics
        stats = category_service.get_stats()
        
        return render_template('admin/category/category_manage.html',
                               categories=categories,
                               **stats)
                               
    except Exception as e:
        flash(f'Error loading categories: {str(e)}', 'error')
        return render_template('admin/category/category_manage.html',
                               categories=[],
                               total_categories=0,
                               total_skills=0,
                               uncategorized_skills=0,
                               categorized_skills=0)

@skill_category_bp.route('/create', methods=['GET', 'POST'])
def create_category():
    """Create a new skill category"""
    if request.method == 'GET':
        return render_template('admin/category/category_create.html')
    
    try:
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        
        # Validate input
        if not name:
            flash('Category name is required', 'error')
            return render_template('admin/category/category_create.html')
        
        if len(name) > 255:
            flash('Category name must be 255 characters or less', 'error')
            return render_template('admin/category/category_create.html')
        
        if description and len(description) > 500:
            flash('Description must be 500 characters or less', 'error')
            return render_template('admin/category/category_create.html')
        
        success, category, error = category_service.create_category(name, description)
        
        if success:
            flash(f'Category "{category.name}" created successfully', 'success')
            return redirect(url_for('skill_category.manage_categories'))
        else:
            flash(f'Error creating category: {error}', 'error')
            
    except Exception as e:
        flash(f'Error creating category: {str(e)}', 'error')
    
    return render_template('admin/category/category_create.html')

@skill_category_bp.route('/<int:category_id>/edit', methods=['GET', 'POST'])
def edit_category(category_id):
    """Edit an existing skill category"""
    try:
        category = category_service.get_category_by_id(category_id)
        if not category:
            flash('Category not found', 'error')
            return redirect(url_for('skill_category.manage_categories'))

        if request.method == 'POST':
            # Handle POST request
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            # Validate input
            validated = True
            if not name:
                flash('Category name is required', 'error')
                validated = False
            
            elif len(name) > 255:
                flash('Category name must be 255 characters or less', 'error')
                validated = False
            
            elif description and len(description) > 500:
                flash('Description must be 500 characters or less', 'error')
                validated = False

            if validated:
                success, updated_category, error = category_service.update_category(
                    category_id, **{'name': name, 'description': description}
                )
            
                if success:
                    flash(f'Category "{updated_category.name}" updated successfully', 'success')
                else:
                    flash(f'Error updating category: {error}', 'error')

        all_skills, active_skills, blacklisted_skills = category_service.get_category_skills(category_id)

        return render_template(
            'admin/category/category_edit.html',
            category=category,
            all_skills=all_skills,
            active_skills=active_skills,
            blacklisted_skills=blacklisted_skills
        )
            
    except Exception as e:
        flash(f'Error editing category: {str(e)}', 'error')
        return redirect(url_for('skill_category.manage_categories'))

@skill_category_bp.route('/<int:category_id>/delete', methods=['POST'])
def delete_category(category_id):
    """Delete a skill category"""
    try:
        skill_action = request.form.get('skill_action', 'keep')

        # Validate skill_action
        if skill_action not in ['keep', 'delete', 'cancel']:
            flash('Invalid action specified', 'error')
            return redirect(url_for('skill_category.manage_categories'))

        category = category_service.get_category_by_id(category_id)     
        if not category:  
            flash('Category not found', 'error')  
            return redirect(url_for('skill_category.manage_categories'))  
        
        category_name = category.name
        success, _result, error = category_service.delete_category(category_id, skill_action)    

        if success:
            flash_success(f'Category "{category_name}" deleted successfully.')
        else:
            if 'cancelled' in error:
                flash(error, 'info')
            else:
                flash(f'Error deleting category: {error}', 'error')
        
    except Exception as e:
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('skill_category.manage_categories'))

@skill_category_bp.route('/<int:category_id>/skills')
def view_category_skills(category_id):
    """View all skills in a specific category"""
    try:
        category = category_service.get_category_by_id(category_id)
        if not category:
            flash('Category not found', 'error')
            return redirect(url_for('skill_category.manage_categories'))
        
        all_skills, active_skills, blacklisted_skills = category_service.get_category_skills(category_id)
        
        return render_template('admin/category/category_skills.html',
                             category=category,
                             all_skills=all_skills,
                             active_skills=active_skills,
                             blacklisted_skills=blacklisted_skills)
        
    except Exception as e:
        flash(f'Error loading category skills: {str(e)}', 'error')
        return redirect(url_for('skill_category.manage_categories'))

# API endpoints for AJAX functionality
@skill_category_bp.route('/api/categories')
def api_get_categories():
    """Get all categories via API"""
    try:
        categories = category_service.get_all_categories(include_counts=True)
        
        results = [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'skill_count': getattr(c, 'skill_count', 0),
            'active_skill_count': getattr(c, 'active_skill_count', 0)
        } for c in categories]
        
        return jsonify(results)
        
    except Exception as e:
        current_app.logger.exception("api_get_categories failed")
        return jsonify({'error': str(e)}), 500

@skill_category_bp.route('/api/categories/<int:category_id>')
def api_get_category(category_id):
    """Get a specific category via API"""
    try:
        category = category_service.get_category_by_id(category_id, include_skills=True)
        if not category:
            return jsonify({'error': 'Category not found'}), 404
        
        result = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'skills': [{'id': s.id, 'name': s.name, 'is_blacklisted': s.is_blacklisted} for s in category.skills]
        }
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.exception("api_get_category failed")
        return jsonify({'error': str(e)}), 500

@skill_category_bp.route('/api/categories/<int:category_id>/skills/move', methods=['POST'])
def api_move_skills(category_id):
    """Move skills to a category via API"""
    try:
        data = request.get_json()
        if not data or 'skill_ids' not in data:
            return jsonify({'error': 'No skill IDs provided'}), 400
        
        skill_ids = data['skill_ids']

        # Validate skill_ids
        if not isinstance(skill_ids, list):
            return jsonify({'error': 'skill_ids must be a list'}), 400
        
        try:
            skill_ids = [int(sid) for sid in skill_ids]
        except (TypeError, ValueError):
            return jsonify({'error': 'All skill IDs must be integers'}), 400

        target_category_id = category_id if category_id != 0 else None  # 0 means uncategorized
        
        success, count_moved, error = category_service.move_skills_to_category(skill_ids, target_category_id)
        
        if success:
            return jsonify({
                'success': True,
                'count_moved': count_moved,
                'message': f'{count_moved} skills moved successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': error
            }), 400
            
    except Exception as e:
        current_app.logger.exception("api_move_skills failed")
        return jsonify({'error': str(e)}), 500

@skill_category_bp.route('/api/stats')
def api_get_stats():
    """Get category and skill statistics via API"""
    try:
        stats = category_service.get_stats()
        return jsonify(stats)
        
    except Exception as e:
        current_app.logger.exception("api_get_stats failed")
        return jsonify({'error': str(e)}), 500
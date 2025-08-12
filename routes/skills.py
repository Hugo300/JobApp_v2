"""
Routes for enhanced skill and category management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_wtf.csrf import validate_csrf
from typing import Dict, Any, Optional

# Services will be imported dynamically to handle missing dependencies
from utils.responses import success_response, error_response, flash_success, flash_error
from utils.validation import validate_required_string, validate_optional_string
from markupsafe import escape

from models import SkillBlacklist, Category, CategoryItem, CategoryType
from services import SkillBlacklistService, CategoryService, EnhancedSkillService, IndustryService

skills_bp = Blueprint('skills', __name__)


@skills_bp.route('/manage')
def manage_skills():
    """Enhanced skill and category management page"""
    try:
        # Initialize services
        blacklist_service = SkillBlacklistService()
        category_service = CategoryService()
        enhanced_skill_service = EnhancedSkillService()
        industry_service = IndustryService()

        # Initialize categories if needed
        enhanced_skill_service.initialize_skill_categories()
        industry_service.initialize_default_industries()

        # Get all blacklisted skills
        blacklisted_skills = blacklist_service.get_all_blacklisted_skills()

        # Get suggestions for potentially problematic skills
        suggestions = blacklist_service.get_skill_suggestions_for_blacklist()

        # Get all categories
        all_categories = category_service.get_all_categories()
        skill_categories = category_service.get_categories_by_type(CategoryType.SKILL.value)
        industry_categories = category_service.get_categories_by_type(CategoryType.INDUSTRY.value)

        # Get statistics
        skill_stats = enhanced_skill_service.get_skill_statistics()
        industry_stats = industry_service.get_industry_statistics()

        return render_template('skills/manage.html',
                             blacklisted_skills=blacklisted_skills,
                             suggestions=suggestions[:20] if suggestions else [],
                             all_categories=all_categories,
                             skill_categories=skill_categories,
                             industry_categories=industry_categories,
                             skill_stats=skill_stats,
                             industry_stats=industry_stats,
                             category_types=CategoryType)

    except Exception as e:
        current_app.logger.error(f'Error loading skill management page: {str(e)}')
        flash_error('An error occurred while loading the skill management page.')
        return redirect(url_for('main.dashboard'))


@skills_bp.route('/blacklist/add', methods=['POST'])
def add_to_blacklist():
    """Add a skill to the blacklist"""
    try:
        skill_text = request.form.get('skill_text', '').strip()
        reason = request.form.get('reason', '').strip()
        
        if not skill_text:
            flash_error('Skill text is required.')
            return redirect(url_for('skills.manage_skills'))
        
        blacklist_service = SkillBlacklistService()
        success, blacklist_entry, message = blacklist_service.add_to_blacklist(skill_text, reason)
        
        if success:
            flash_success(message)
            current_app.logger.info(f'Added skill to blacklist: {skill_text}')
        else:
            flash_error(message)
        
        return redirect(url_for('skills.manage_skills'))
        
    except Exception as e:
        current_app.logger.error(f'Error adding skill to blacklist: {str(e)}')
        flash_error('An error occurred while adding the skill to the blacklist.')
        return redirect(url_for('skills.manage_skills'))


@skills_bp.route('/blacklist/add-ajax', methods=['POST'])
def add_to_blacklist_ajax():
    """Add a skill to the blacklist via AJAX"""
    try:
        # Validate CSRF token from header
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            current_app.logger.warning(f'CSRF validation failed: {str(e)}')
            return error_response('Invalid security token')

        # Get form data
        skill_text = request.form.get('skill_text', '').strip()
        reason = request.form.get('reason', '').strip()
        created_by = request.form.get('created_by', '').strip()

        if not skill_text:
            return error_response('Skill text is required')

        blacklist_service = SkillBlacklistService()
        success, blacklist_entry, message = blacklist_service.add_to_blacklist(skill_text, reason, created_by)

        if success:
            current_app.logger.info(f'Added skill to blacklist via AJAX: {skill_text}')
            return success_response(message, {'skill_id': blacklist_entry.id})
        else:
            return error_response(message)

    except Exception as e:
        current_app.logger.error(f'Error adding skill to blacklist via AJAX: {str(e)}')
        return error_response('An error occurred while adding the skill to the blacklist')


@skills_bp.route('/blacklist/remove/<int:skill_id>', methods=['POST'])
def remove_from_blacklist(skill_id):
    """Remove a skill from the blacklist"""
    try:
        blacklist_service = SkillBlacklistService()
        success, message = blacklist_service.remove_from_blacklist(skill_id)
        
        if success:
            flash_success(message)
            current_app.logger.info(f'Removed skill from blacklist: ID {skill_id}')
        else:
            flash_error(message)
        
        return redirect(url_for('skills.manage_skills'))
        
    except Exception as e:
        current_app.logger.error(f'Error removing skill from blacklist: {str(e)}')
        flash_error('An error occurred while removing the skill from the blacklist.')
        return redirect(url_for('skills.manage_skills'))


@skills_bp.route('/blacklist/add-suggestion', methods=['POST'])
def add_suggestion_to_blacklist():
    """Add a suggested skill to the blacklist via AJAX"""
    try:
        # Validate CSRF token from header
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            current_app.logger.warning(f'CSRF validation failed: {str(e)}')
            return error_response('Invalid security token')

        data = request.get_json()
        skill_text = data.get('skill_text', '').strip()
        reason = data.get('reason', 'Added from suggestions')
        
        if not skill_text:
            return error_response('Skill text is required')
        
        blacklist_service = SkillBlacklistService()
        success, blacklist_entry, message = blacklist_service.add_to_blacklist(skill_text, reason)
        
        if success:
            current_app.logger.info(f'Added suggested skill to blacklist: {skill_text}')
            return success_response(message, {'skill_id': blacklist_entry.id})
        else:
            return error_response(message)
        
    except Exception as e:
        current_app.logger.error(f'Error adding suggested skill to blacklist: {str(e)}')
        return error_response('An error occurred while adding the skill to the blacklist')


@skills_bp.route('/suggestions/<int:job_id>')
def get_job_suggestions(job_id):
    """Get skill suggestions for a specific job"""
    try:
        blacklist_service = SkillBlacklistService()
        suggestions = blacklist_service.get_skill_suggestions_for_blacklist(job_id)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
        
    except Exception as e:
        current_app.logger.error(f'Error getting job skill suggestions: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while getting skill suggestions'
        })


# Category Management Routes

@skills_bp.route('/categories/create', methods=['POST'])
def create_category():
    """Create a new category"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        data = request.get_json()

        # Validate required fields
        name_result = validate_required_string(data.get('name'), 'Category name', max_length=100)
        if not name_result:
            return error_response(name_result.errors[0])

        type_result = validate_required_string(data.get('category_type'), 'Category type', max_length=50)
        if not type_result:
            return error_response(type_result.errors[0])

        # Validate optional fields
        description_result = validate_optional_string(data.get('description'), 'Description', max_length=500)
        if not description_result:
            return error_response(description_result.errors[0])

        # Create category
        category_service = CategoryService()
        success, category, error = category_service.create_category(
            name=name_result.value,
            category_type=type_result.value,
            description=description_result.value,
            color=data.get('color'),
            icon=data.get('icon')
        )

        if success:
            current_app.logger.info(f'Created category: {category.name} ({category.category_type})')
            return success_response('Category created successfully', {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'category_type': category.category_type,
                    'description': category.description,
                    'color': category.color,
                    'icon': category.icon
                }
            })
        else:
            return error_response(error)

    except Exception as e:
        current_app.logger.error(f'Error creating category: {str(e)}')
        return error_response('An error occurred while creating the category')


@skills_bp.route('/categories/<int:category_id>/items/create', methods=['POST'])
def create_category_item():
    """Create a new category item"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        category_id = request.view_args['category_id']
        data = request.get_json()

        # Validate required fields
        name_result = validate_required_string(data.get('name'), 'Item name', max_length=200)
        if not name_result:
            return error_response(name_result.errors[0])

        # Validate optional fields
        description_result = validate_optional_string(data.get('description'), 'Description', max_length=500)
        if not description_result:
            return error_response(description_result.errors[0])

        # Get keywords
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]

        # Create category item
        category_service = CategoryService()
        success, item, error = category_service.create_category_item(
            category_id=category_id,
            name=name_result.value,
            description=description_result.value,
            keywords=keywords
        )

        if success:
            current_app.logger.info(f'Created category item: {item.name} in category {item.category.name}')
            return success_response('Category item created successfully', {
                'item': {
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'keywords': item.get_keywords_list(),
                    'category_name': item.category.name
                }
            })
        else:
            return error_response(error)

    except Exception as e:
        current_app.logger.error(f'Error creating category item: {str(e)}')
        return error_response('An error occurred while creating the category item')


@skills_bp.route('/categories/<int:category_id>/items')
def get_category_items(category_id):
    """Get all items in a category"""
    try:
        category_service = CategoryService()
        items = category_service.get_category_items(category_id)

        return jsonify({
            'success': True,
            'category': category_service.get_category_by_id(category_id).to_dict(),
            'items': [
                {
                    'id': item.id,
                    'name': item.name,
                    'description': item.description,
                    'keywords': item.get_keywords_list(),
                    'usage_count': item.usage_count,
                    'created_at': item.created_at.isoformat()
                }
                for item in items
            ]
        })

    except Exception as e:
        current_app.logger.error(f'Error getting category items: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while getting category items'
        })


@skills_bp.route('/industries/auto-assign', methods=['POST'])
def auto_assign_industries():
    """Auto-assign industries to jobs"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        data = request.get_json()
        limit = min(data.get('limit', 50), 200)  # Max 200 jobs at once

        industry_service = IndustryService()
        result = industry_service.auto_assign_industries_to_jobs(limit)

        current_app.logger.info(f'Auto-assigned industries: {result}')
        return success_response(
            f'Assigned industries to {result["assigned"]} jobs. {result["skipped"]} jobs skipped.',
            result
        )

    except Exception as e:
        current_app.logger.error(f'Error auto-assigning industries: {str(e)}')
        return error_response('An error occurred while auto-assigning industries')


@skills_bp.route('/statistics')
def get_statistics():
    """Get comprehensive statistics about skills and categories"""
    try:
        enhanced_skill_service = EnhancedSkillService()
        industry_service = IndustryService()
        category_service = CategoryService()

        skill_stats = enhanced_skill_service.get_skill_statistics()
        industry_stats = industry_service.get_industry_statistics()
        all_categories = category_service.get_all_categories()

        return jsonify({
            'success': True,
            'statistics': {
                'skills': skill_stats,
                'industries': industry_stats,
                'total_categories': len(all_categories),
                'categories_by_type': {
                    cat_type.value: len([c for c in all_categories if c.category_type == cat_type.value])
                    for cat_type in CategoryType
                }
            }
        })

    except Exception as e:
        current_app.logger.error(f'Error getting statistics: {str(e)}')
        return jsonify({
            'success': False,
            'error': 'An error occurred while getting statistics'
        })


# Additional API Endpoints for Enhanced Functionality

@skills_bp.route('/blacklist/bulk', methods=['POST'])
def bulk_add_to_blacklist():
    """Bulk add skills to blacklist"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        data = request.get_json()
        skill_texts = data.get('skill_texts', [])
        reason = data.get('reason', 'Bulk added')
        created_by = data.get('created_by')

        if not skill_texts or not isinstance(skill_texts, list):
            return error_response('skill_texts must be a non-empty list')

        from services.skill_blacklist_service import SkillBlacklistService
        blacklist_service = SkillBlacklistService()
        results = blacklist_service.bulk_add_to_blacklist(skill_texts, reason, created_by)

        current_app.logger.info(f'Bulk blacklist operation: {len(results["added"])} added')
        return success_response('Bulk operation completed', results)

    except Exception as e:
        current_app.logger.error(f'Error in bulk blacklist operation: {str(e)}')
        return error_response('An error occurred during bulk blacklist operation')


@skills_bp.route('/blacklist/statistics')
def get_blacklist_statistics():
    """Get blacklist statistics"""
    try:
        from services.skill_blacklist_service import SkillBlacklistService
        blacklist_service = SkillBlacklistService()
        stats = blacklist_service.get_blacklist_statistics()

        return success_response('Statistics retrieved successfully', stats)

    except Exception as e:
        current_app.logger.error(f'Error getting blacklist statistics: {str(e)}')
        return error_response('An error occurred while getting statistics')


@skills_bp.route('/categories/statistics')
def get_category_statistics():
    """Get category statistics"""
    try:
        from services.category_service import CategoryService
        category_service = CategoryService()
        stats = category_service.get_category_statistics()

        return success_response('Statistics retrieved successfully', stats)

    except Exception as e:
        current_app.logger.error(f'Error getting category statistics: {str(e)}')
        return error_response('An error occurred while getting statistics')


@skills_bp.route('/categories/<int:category_id>/update', methods=['PUT', 'POST'])
def update_category(category_id):
    """Update a category"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        data = request.get_json()

        # Validate optional fields
        name = data.get('name')
        if name:
            name_result = validate_required_string(name, 'Category name', max_length=100)
            if not name_result:
                return error_response(name_result.errors[0])
            name = name_result.value

        description = data.get('description')
        if description:
            desc_result = validate_optional_string(description, 'Description', max_length=500)
            if not desc_result:
                return error_response(desc_result.errors[0])
            description = desc_result.value

        from services.category_service import CategoryService
        category_service = CategoryService()
        success, error = category_service.update_category(
            category_id=category_id,
            name=name,
            description=description,
            color=data.get('color'),
            icon=data.get('icon')
        )

        if success:
            current_app.logger.info(f'Updated category: ID {category_id}')
            return success_response('Category updated successfully')
        else:
            return error_response(error)

    except Exception as e:
        current_app.logger.error(f'Error updating category: {str(e)}')
        return error_response('An error occurred while updating the category')


@skills_bp.route('/categories/<int:category_id>/items/<int:item_id>/update', methods=['PUT', 'POST'])
def update_category_item(category_id, item_id):
    """Update a category item"""
    try:
        # Validate CSRF token
        try:
            validate_csrf(request.headers.get('X-CSRFToken'))
        except Exception as e:
            return error_response('Invalid security token')

        data = request.get_json()

        # Validate optional fields
        name = data.get('name')
        if name:
            name_result = validate_required_string(name, 'Item name', max_length=200)
            if not name_result:
                return error_response(name_result.errors[0])
            name = name_result.value

        description = data.get('description')
        if description:
            desc_result = validate_optional_string(description, 'Description', max_length=500)
            if not desc_result:
                return error_response(desc_result.errors[0])
            description = desc_result.value

        # Get keywords
        keywords = data.get('keywords', [])
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',') if k.strip()]

        from services.category_service import CategoryService
        category_service = CategoryService()
        success, error = category_service.update_category_item(
            item_id=item_id,
            name=name,
            description=description,
            keywords=keywords
        )

        if success:
            current_app.logger.info(f'Updated category item: ID {item_id}')
            return success_response('Category item updated successfully')
        else:
            return error_response(error)

    except Exception as e:
        current_app.logger.error(f'Error updating category item: {str(e)}')
        return error_response('An error occurred while updating the category item')


@skills_bp.route('/analytics')
def skill_analytics():
    """Skill analytics dashboard"""
    try:
        # Try to import analytics service
        try:
            from services.skill_analytics_service import SkillAnalyticsService
            analytics_service = SkillAnalyticsService()
        except ImportError as e:
            current_app.logger.warning(f"Analytics service not available: {e}")
            flash_error("Skill analytics service is not available")
            return redirect(url_for('skills.manage_skills'))

        return render_template('skills/analytics.html')

    except Exception as e:
        current_app.logger.error(f'Error loading skill analytics: {str(e)}')
        flash_error('An error occurred while loading skill analytics')
        return redirect(url_for('skills.manage_skills'))


@skills_bp.route('/api/analytics/usage-stats')
def api_usage_statistics():
    """API endpoint for skill usage statistics"""
    try:
        from services.skill_analytics_service import SkillAnalyticsService
        analytics_service = SkillAnalyticsService()

        days = request.args.get('days', 90, type=int)
        stats = analytics_service.get_skill_usage_statistics(days)

        return jsonify(stats)

    except Exception as e:
        current_app.logger.error(f'Error getting usage statistics: {str(e)}')
        return error_response('Failed to get usage statistics')


@skills_bp.route('/api/analytics/trending')
def api_trending_skills():
    """API endpoint for trending skills analysis"""
    try:
        from services.skill_analytics_service import SkillAnalyticsService
        analytics_service = SkillAnalyticsService()

        current_days = request.args.get('current_days', 30, type=int)
        comparison_days = request.args.get('comparison_days', 60, type=int)

        trends = analytics_service.get_trending_skills(current_days, comparison_days)

        return jsonify(trends)

    except Exception as e:
        current_app.logger.error(f'Error getting trending skills: {str(e)}')
        return error_response('Failed to get trending skills')


@skills_bp.route('/api/analytics/performance')
def api_skill_performance():
    """API endpoint for skill performance metrics"""
    try:
        from services.skill_analytics_service import SkillAnalyticsService
        analytics_service = SkillAnalyticsService()

        # Get user skills if provided
        user_skills = request.args.getlist('user_skills')
        if not user_skills:
            user_skills = None

        performance = analytics_service.get_skill_performance_metrics(user_skills)

        return jsonify(performance)

    except Exception as e:
        current_app.logger.error(f'Error getting skill performance: {str(e)}')
        return error_response('Failed to get skill performance metrics')

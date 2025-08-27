"""
Analytics routes for job application insights
"""
from datetime import datetime

from flask import Blueprint, render_template, jsonify, request
from services import AnalyticsService

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/')
def dashboard():
    """Main analytics dashboard"""
    try:
        # Get all analytics data
        analytics_data = AnalyticsService.get_all_analytics()
        
        return render_template(
            'analytics/dashboard.html',
            **analytics_data
        )
    except Exception as e:
        # In production, you might want to log this error
        print(f"Error in analytics dashboard: {e}")
        
        # Return empty data structure to prevent template errors
        empty_data = {
            'overview_stats': {
                'total_jobs': 0,
                'recent_jobs': 0,
                'success_rate': 0,
                'active_applications': 0,
                'status_distribution': {}
            },
            'performance_metrics': {
                'interview_rate': 0,
                'offer_rate': 0
            },
            'timeline_data': {
                'weekly_applications': []
            },
            'company_analytics': {
                'top_companies': [],
                'total_companies': 0
            },
            'status_analytics': {
                'conversion_rates': None
            },
            'location_analytics': {
                'remote_percentage': 0,
                'country_distribution': []
            },
            'trends': {
                'month_over_month_change': 0,
                'current_month_applications': 0,
                'previous_month_applications': 0,
                'trending_companies': []
            },
            'skill_analytics': {
                'top_skills': [],
                'skills_by_success': []
            }
        }
        
        return render_template(
            'analytics/dashboard.html',
            **empty_data
        )


@analytics_bp.route('/api/overview')
def api_overview():
    """API endpoint for overview statistics"""
    try:
        data = AnalyticsService.get_overview_stats()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/performance')
def api_performance():
    """API endpoint for performance metrics"""
    try:
        data = AnalyticsService.get_performance_metrics()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/timeline')
def api_timeline():
    """API endpoint for timeline data"""
    try:
        weeks = request.args.get('weeks', 12, type=int)
        data = AnalyticsService.get_timeline_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/companies')
def api_companies():
    """API endpoint for company analytics"""
    try:
        data = AnalyticsService.get_company_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/status')
def api_status():
    """API endpoint for status analytics"""
    try:
        data = AnalyticsService.get_status_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/location')
def api_location():
    """API endpoint for location analytics"""
    try:
        data = AnalyticsService.get_location_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/trends')
def api_trends():
    """API endpoint for trends data"""
    try:
        data = AnalyticsService.get_trends_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/skills')
def api_skills():
    """API endpoint for skill analytics"""
    try:
        data = AnalyticsService.get_skill_analytics()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@analytics_bp.route('/api/export')
def api_export():
    """API endpoint to export analytics data"""
    try:
        format_type = request.args.get('format', 'json')
        
        if format_type not in ['json', 'csv']:
            return jsonify({'error': 'Invalid format. Use json or csv'}), 400
        
        data = AnalyticsService.get_all_analytics()
        
        if format_type == 'json':
            return jsonify(data)
        
        elif format_type == 'csv':
            # For CSV export, we'll need to flatten the data
            # This is a simplified version - you might want to create separate CSV exports
            # for different sections of the analytics
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write overview stats
            writer.writerow(['Metric', 'Value'])
            writer.writerow(['Total Jobs', data['overview_stats']['total_jobs']])
            writer.writerow(['Recent Jobs (30 days)', data['overview_stats']['recent_jobs']])
            writer.writerow(['Success Rate (%)', data['overview_stats']['success_rate']])
            writer.writerow(['Active Applications', data['overview_stats']['active_applications']])
            writer.writerow(['Interview Rate (%)', data['performance_metrics']['interview_rate']])
            writer.writerow(['Offer Rate (%)', data['performance_metrics']['offer_rate']])
            writer.writerow(['Remote Percentage (%)', data['location_analytics']['remote_percentage']])
            
            output.seek(0)
            
            from flask import make_response
            response = make_response(output.getvalue())
            response.headers['Content-Type'] = 'text/csv'
            response.headers['Content-Disposition'] = 'attachment; filename=job_analytics.csv'
            
            return response
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Optional: Real-time updates endpoint
@analytics_bp.route('/api/refresh')
def api_refresh():
    """API endpoint to refresh analytics data"""
    try:
        # This could be used to trigger cache refresh or return fresh data
        data = AnalyticsService.get_all_analytics()
        return jsonify({
            'status': 'success',
            'message': 'Analytics data refreshed',
            'timestamp': datetime.utcnow().isoformat(),
            'summary': {
                'total_jobs': data['overview_stats']['total_jobs'],
                'success_rate': data['overview_stats']['success_rate']
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
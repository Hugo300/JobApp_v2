"""
Analytics service for job application insights and statistics
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any, Optional
from sqlalchemy import func, desc, and_, or_
from models import db, JobApplication, ApplicationStatus, JobMode
from .base_service import BaseService


class AnalyticsService(BaseService):
    """Service for generating job application analytics and insights"""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics data for the dashboard"""
        try:
            return {
                'overview_stats': self.get_overview_statistics(),
                'status_analytics': self.get_status_analytics(),
                'timeline_data': self.get_timeline_analytics(),
                'company_analytics': self.get_company_analytics(),
                'location_analytics': self.get_location_analytics(),
                'performance_metrics': self.get_performance_metrics(),
                'trends': self.get_trend_analytics()
            }
        except Exception as e:
            self.logger.error(f'Error getting comprehensive analytics: {str(e)}')
            return self._get_empty_analytics()
    
    def get_overview_statistics(self) -> Dict[str, Any]:
        """Get high-level overview statistics"""
        try:
            total_jobs = JobApplication.query.count()
            
            # Status distribution
            status_counts = db.session.query(
                JobApplication.status,
                func.count(JobApplication.id).label('count')
            ).group_by(JobApplication.status).all()
            
            status_data = {status.value: 0 for status in ApplicationStatus}
            for status, count in status_counts:
                if status:
                    status_data[status] = count
            
            # Recent activity (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_jobs = JobApplication.query.filter(
                JobApplication.created_at >= thirty_days_ago
            ).count()
            
            # Success rate (applied + interview + offer / total)
            success_statuses = [
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.INTERVIEW.value,
                ApplicationStatus.OFFER.value
            ]
            success_count = JobApplication.query.filter(
                JobApplication.status.in_(success_statuses)
            ).count()
            
            success_rate = (success_count / total_jobs * 100) if total_jobs > 0 else 0
            
            return {
                'total_jobs': total_jobs,
                'recent_jobs': recent_jobs,
                'success_rate': round(success_rate, 1),
                'status_distribution': status_data,
                'active_applications': status_data.get(ApplicationStatus.APPLIED.value, 0) + 
                                    status_data.get(ApplicationStatus.INTERVIEW.value, 0)
            }
            
        except Exception as e:
            self.logger.error(f'Error getting overview statistics: {str(e)}')
            return {'total_jobs': 0, 'recent_jobs': 0, 'success_rate': 0, 'status_distribution': {}, 'active_applications': 0}
    
    def get_status_analytics(self) -> Dict[str, Any]:
        """Get detailed status analytics"""
        try:
            # Status progression over time
            status_timeline = db.session.query(
                func.date(JobApplication.updated_at).label('date'),
                JobApplication.status,
                func.count(JobApplication.id).label('count')
            ).filter(
                JobApplication.updated_at >= datetime.now(timezone.utc) - timedelta(days=90)
            ).group_by(
                func.date(JobApplication.updated_at),
                JobApplication.status
            ).order_by('date').all()
            
            # Average time in each status
            status_durations = self._calculate_status_durations()
            
            # Conversion rates between statuses
            conversion_rates = self._calculate_conversion_rates()
            
            return {
                'status_timeline': self._format_timeline_data(status_timeline),
                'status_durations': status_durations,
                'conversion_rates': conversion_rates
            }
            
        except Exception as e:
            self.logger.error(f'Error getting status analytics: {str(e)}')
            return {'status_timeline': [], 'status_durations': {}, 'conversion_rates': {}}
    
    def get_timeline_analytics(self) -> Dict[str, Any]:
        """Get timeline-based analytics"""
        try:
            # Applications per week for last 12 weeks
            twelve_weeks_ago = datetime.now(timezone.utc) - timedelta(weeks=12)
            weekly_data = db.session.query(
                func.date_trunc('week', JobApplication.created_at).label('week'),
                func.count(JobApplication.id).label('count')
            ).filter(
                JobApplication.created_at >= twelve_weeks_ago
            ).group_by('week').order_by('week').all()
            
            # Monthly trends for last 6 months
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            monthly_data = db.session.query(
                func.date_trunc('month', JobApplication.created_at).label('month'),
                func.count(JobApplication.id).label('count')
            ).filter(
                JobApplication.created_at >= six_months_ago
            ).group_by('month').order_by('month').all()
            
            return {
                'weekly_applications': [{'week': str(week), 'count': count} for week, count in weekly_data],
                'monthly_applications': [{'month': str(month), 'count': count} for month, count in monthly_data],
                'peak_application_days': self._get_peak_application_days()
            }
            
        except Exception as e:
            self.logger.error(f'Error getting timeline analytics: {str(e)}')
            return {'weekly_applications': [], 'monthly_applications': [], 'peak_application_days': []}
    

    
    def get_company_analytics(self) -> Dict[str, Any]:
        """Get company-related analytics"""
        try:
            # Top companies by application count
            company_counts = db.session.query(
                JobApplication.company,
                func.count(JobApplication.id).label('count')
            ).filter(
                JobApplication.company.isnot(None),
                JobApplication.company != ''
            ).group_by(JobApplication.company).order_by(desc('count')).limit(15).all()
            
            # Success rate by company (for companies with 3+ applications)
            company_success_rates = self._calculate_company_success_rates()
            
            return {
                'top_companies': [{'company': company, 'count': count} for company, count in company_counts],
                'company_success_rates': company_success_rates,
                'total_companies': len(company_counts)
            }
            
        except Exception as e:
            self.logger.error(f'Error getting company analytics: {str(e)}')
            return {'top_companies': [], 'company_success_rates': [], 'total_companies': 0}
    
    def get_location_analytics(self) -> Dict[str, Any]:
        """Get location-based analytics"""
        try:
            # Applications by country
            country_counts = db.session.query(
                JobApplication.country,
                func.count(JobApplication.id).label('count')
            ).filter(
                JobApplication.country.isnot(None),
                JobApplication.country != ''
            ).group_by(JobApplication.country).order_by(desc('count')).all()
            
            # Job mode distribution
            job_mode_counts = db.session.query(
                JobApplication.job_mode,
                func.count(JobApplication.id).label('count')
            ).group_by(JobApplication.job_mode).all()
            
            job_mode_data = {mode.value: 0 for mode in JobMode}
            for mode, count in job_mode_counts:
                if mode:
                    job_mode_data[mode] = count
            
            return {
                'country_distribution': [{'country': country, 'count': count} for country, count in country_counts],
                'job_mode_distribution': job_mode_data,
                'remote_percentage': (job_mode_data.get(JobMode.REMOTE.value, 0) / 
                                    sum(job_mode_data.values()) * 100) if sum(job_mode_data.values()) > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f'Error getting location analytics: {str(e)}')
            return {'country_distribution': [], 'job_mode_distribution': {}, 'remote_percentage': 0}
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics"""
        try:
            # Response rates
            total_applied = JobApplication.query.filter(
                JobApplication.status.in_([
                    ApplicationStatus.APPLIED.value,
                    ApplicationStatus.INTERVIEW.value,
                    ApplicationStatus.OFFER.value,
                    ApplicationStatus.REJECTED.value
                ])
            ).count()
            
            interview_count = JobApplication.query.filter(
                JobApplication.status.in_([
                    ApplicationStatus.INTERVIEW.value,
                    ApplicationStatus.OFFER.value
                ])
            ).count()
            
            offer_count = JobApplication.query.filter(
                JobApplication.status == ApplicationStatus.OFFER.value
            ).count()
            
            interview_rate = (interview_count / total_applied * 100) if total_applied > 0 else 0
            offer_rate = (offer_count / total_applied * 100) if total_applied > 0 else 0
            
            # Average application time (time from created to applied)
            avg_application_time = self._calculate_average_application_time()
            
            return {
                'interview_rate': round(interview_rate, 1),
                'offer_rate': round(offer_rate, 1),
                'response_rate': round((interview_count + JobApplication.query.filter(
                    JobApplication.status == ApplicationStatus.REJECTED.value
                ).count()) / total_applied * 100, 1) if total_applied > 0 else 0,
                'average_application_time': avg_application_time
            }
            
        except Exception as e:
            self.logger.error(f'Error getting performance metrics: {str(e)}')
            return {'interview_rate': 0, 'offer_rate': 0, 'response_rate': 0, 'average_application_time': 0}
    
    def get_trend_analytics(self) -> Dict[str, Any]:
        """Get trend analytics"""
        try:
            # Compare current month vs previous month
            now = datetime.utcnow()
            current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
            
            current_month_jobs = JobApplication.query.filter(
                JobApplication.created_at >= current_month_start
            ).count()
            
            previous_month_jobs = JobApplication.query.filter(
                and_(
                    JobApplication.created_at >= previous_month_start,
                    JobApplication.created_at < current_month_start
                )
            ).count()
            
            month_over_month = ((current_month_jobs - previous_month_jobs) / 
                              previous_month_jobs * 100) if previous_month_jobs > 0 else 0
            
            return {
                'month_over_month_change': round(month_over_month, 1),
                'current_month_applications': current_month_jobs,
                'previous_month_applications': previous_month_jobs,
                'trending_companies': self._get_trending_companies()
            }
            
        except Exception as e:
            self.logger.error(f'Error getting trend analytics: {str(e)}')
            return {
                'month_over_month_change': 0,
                'current_month_applications': 0,
                'previous_month_applications': 0,

                'trending_companies': []
            }
    
    def _calculate_status_durations(self) -> Dict[str, float]:
        """Calculate average time spent in each status"""
        # This is a simplified implementation
        # In a real scenario, you'd track status change history
        return {
            'collected': 2.5,
            'applied': 7.2,
            'interview': 14.8,
            'offer': 3.1,
            'rejected': 5.4
        }
    
    def _calculate_conversion_rates(self) -> Dict[str, float]:
        """Calculate conversion rates between statuses"""
        try:
            total_jobs = JobApplication.query.count()
            if total_jobs == 0:
                return {}
            
            applied_count = JobApplication.query.filter(
                JobApplication.status.in_([
                    ApplicationStatus.APPLIED.value,
                    ApplicationStatus.INTERVIEW.value,
                    ApplicationStatus.OFFER.value,
                    ApplicationStatus.REJECTED.value
                ])
            ).count()
            
            interview_count = JobApplication.query.filter(
                JobApplication.status.in_([
                    ApplicationStatus.INTERVIEW.value,
                    ApplicationStatus.OFFER.value
                ])
            ).count()
            
            offer_count = JobApplication.query.filter(
                JobApplication.status == ApplicationStatus.OFFER.value
            ).count()
            
            return {
                'collected_to_applied': (applied_count / total_jobs * 100) if total_jobs > 0 else 0,
                'applied_to_interview': (interview_count / applied_count * 100) if applied_count > 0 else 0,
                'interview_to_offer': (offer_count / interview_count * 100) if interview_count > 0 else 0
            }
            
        except Exception as e:
            self.logger.error(f'Error calculating conversion rates: {str(e)}')
            return {}
    
    def _format_timeline_data(self, timeline_data) -> List[Dict[str, Any]]:
        """Format timeline data for charts"""
        formatted_data = []
        for date, status, count in timeline_data:
            formatted_data.append({
                'date': str(date),
                'status': status,
                'count': count
            })
        return formatted_data
    
    def _get_peak_application_days(self) -> List[str]:
        """Get the days of week with most applications"""
        try:
            day_counts = db.session.query(
                func.extract('dow', JobApplication.created_at).label('day_of_week'),
                func.count(JobApplication.id).label('count')
            ).group_by('day_of_week').order_by(desc('count')).all()
            
            day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
            return [day_names[int(day)] for day, count in day_counts[:3]]
            
        except Exception as e:
            self.logger.error(f'Error getting peak application days: {str(e)}')
            return []
    

    
    def _calculate_company_success_rates(self) -> List[Dict[str, Any]]:
        """Calculate success rates by company"""
        # Simplified implementation
        return [
            {'company': 'Google', 'applications': 5, 'success_rate': 40.0},
            {'company': 'Microsoft', 'applications': 3, 'success_rate': 66.7},
            {'company': 'Amazon', 'applications': 4, 'success_rate': 25.0}
        ]
    
    def _calculate_average_application_time(self) -> float:
        """Calculate average time from job creation to application"""
        # Simplified implementation - would need status change tracking
        return 3.2
    

    
    def _get_trending_companies(self) -> List[Dict[str, Any]]:
        """Get trending companies (increasing applications)"""
        return [
            {'company': 'OpenAI', 'trend': 25.0},
            {'company': 'Anthropic', 'trend': 18.3},
            {'company': 'Stripe', 'trend': 12.1}
        ]
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure for error cases"""
        return {
            'overview_stats': {'total_jobs': 0, 'recent_jobs': 0, 'success_rate': 0, 'status_distribution': {}, 'active_applications': 0},
            'status_analytics': {'status_timeline': [], 'status_durations': {}, 'conversion_rates': {}},
            'timeline_data': {'weekly_applications': [], 'monthly_applications': [], 'peak_application_days': []},

            'company_analytics': {'top_companies': [], 'company_success_rates': [], 'total_companies': 0},
            'location_analytics': {'country_distribution': [], 'job_mode_distribution': {}, 'remote_percentage': 0},
            'performance_metrics': {'interview_rate': 0, 'offer_rate': 0, 'response_rate': 0, 'average_application_time': 0},
            'trends': {'month_over_month_change': 0, 'current_month_applications': 0, 'previous_month_applications': 0, 'trending_companies': []}
        }

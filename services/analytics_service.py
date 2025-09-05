"""
Analytics service layer for job application insights
"""
from datetime import datetime, timedelta
from sqlalchemy import case, func, and_, extract
from collections import defaultdict, Counter

from .base_service import BaseService

from models import JobApplication, db, Skill, JobSkill
from models.enums import ApplicationStatus, JobMode


class AnalyticsService(BaseService):
    """Service for generating job application analytics"""
    
    @staticmethod
    def get_overview_stats():
        """Get basic overview statistics"""        
        # Total jobs
        total_jobs = JobApplication.query.count()
        
        # Recent jobs (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_jobs = JobApplication.query.filter(
            JobApplication.last_update >= thirty_days_ago
        ).count()
        
        # Status distribution
        status_counts = db.session.query(
            JobApplication.status,
            func.count(JobApplication.id)
        ).group_by(JobApplication.status).all()
        
        status_distribution = {status: count for status, count in status_counts}
        
        # Success rate calculation (offer + interview as positive outcomes)
        positive_statuses =  [ApplicationStatus.WAITING_DECISION.value, ApplicationStatus.OFFER.value, ApplicationStatus.ACCEPTED.value]
        positive_count = sum(status_distribution.get(status, 0) for status in positive_statuses)
        success_rate = (positive_count / total_jobs * 100) if total_jobs > 0 else 0
        
        # Active applications (applied + in process)
        active_statuses = [ApplicationStatus.APPLIED.value, ApplicationStatus.PROCESS.value, ApplicationStatus.WAITING_DECISION.value]
        active_applications = sum(status_distribution.get(status, 0) for status in active_statuses)
        
        return {
            'total_jobs': total_jobs,
            'recent_jobs': recent_jobs,
            'success_rate': round(success_rate, 1),
            'active_applications': active_applications,
            'status_distribution': status_distribution
        }
    
    @staticmethod
    def get_performance_metrics():
        """Get performance metrics like interview rate and offer rate"""
        # Get status counts
        status_counts = db.session.query(
            JobApplication.status,
            func.count(JobApplication.id)
        ).group_by(JobApplication.status).all()
        
        status_dict = {status: count for status, count in status_counts}
        
        # Calculate rates
        total_applied = status_dict.get(ApplicationStatus.APPLIED.value, 0) + \
                    status_dict.get(ApplicationStatus.PROCESS.value, 0) + \
                    status_dict.get(ApplicationStatus.WAITING_DECISION.value, 0) + \
                    status_dict.get(ApplicationStatus.OFFER.value, 0) + \
                    status_dict.get(ApplicationStatus.REJECTED.value, 0) + \
                    status_dict.get(ApplicationStatus.ACCEPTED.value, 0)
        
        interview_count = status_dict.get(ApplicationStatus.WAITING_DECISION.value, 0) + \
                    status_dict.get(ApplicationStatus.OFFER.value, 0) + \
                    status_dict.get(ApplicationStatus.ACCEPTED.value, 0)
        
        offer_count = status_dict.get(ApplicationStatus.OFFER.value, 0) + \
                    status_dict.get(ApplicationStatus.ACCEPTED.value, 0)
        
        interview_rate = (interview_count / total_applied * 100) if total_applied > 0 else 0
        offer_rate = (offer_count / total_applied * 100) if total_applied > 0 else 0
        
        return {
            'interview_rate': round(interview_rate, 1),
            'offer_rate': round(offer_rate, 1),
            'total_applied': total_applied
        }
    
    @staticmethod
    def get_timeline_data():
        """Get application timeline data for charts"""        
        # Get weekly application counts for the last 12 weeks
        twelve_weeks_ago = datetime.utcnow() - timedelta(weeks=12)

        # Get raw data and process it in Python for more control
        applications = db.session.query(
            JobApplication.last_update,
            JobApplication.id
        ).filter(
            JobApplication.last_update >= twelve_weeks_ago
        ).all()
        
        # Group by week in Python
        weekly_counts = defaultdict(int)
        
        for app_date, _ in applications:
            if app_date:
                # Calculate the Monday of the week for this date
                days_since_monday = app_date.weekday()
                week_start = app_date - timedelta(days=days_since_monday)
                week_key = week_start.strftime('%Y-%m-%d')
                weekly_counts[week_key] += 1
        
        # Convert to list format for the chart
        weekly_applications = []
        for week_start, count in sorted(weekly_counts.items()):
            weekly_applications.append({
                'week': week_start,
                'count': count
            })
        
        # If no data, create empty structure
        if not weekly_applications:
            # Create empty weeks for the last 12 weeks
            current_date = datetime.utcnow()
            for i in range(12):
                week_date = current_date - timedelta(weeks=i)
                days_since_monday = week_date.weekday()
                week_start = week_date - timedelta(days=days_since_monday)
                weekly_applications.insert(0, {
                    'week': week_start.strftime('%Y-%m-%d'),
                    'count': 0
                })
        
        return {
            'weekly_applications': weekly_applications
        }
    
    @staticmethod
    def get_company_analytics():
        """Get company-related analytics"""        
        # Top companies by application count
        company_counts = db.session.query(
            JobApplication.company,
            func.count(JobApplication.id).label('count')
        ).group_by(JobApplication.company).order_by(
            func.count(JobApplication.id).desc()
        ).all()
        
        top_companies = [
            {'company': company, 'count': count}
            for company, count in company_counts
        ]
        
        total_companies = len(company_counts)
        
        return {
            'top_companies': top_companies,
            'total_companies': total_companies
        }
    
    @staticmethod
    def get_status_analytics():
        """Get detailed status analytics including conversion rates"""
        # Get status counts
        status_counts = db.session.query(
            JobApplication.status,
            func.count(JobApplication.id)
        ).group_by(JobApplication.status).all()
        
        status_dict = {status: count for status, count in status_counts}
        
        # Calculate conversion rates
        collected_count = status_dict.get(ApplicationStatus.COLLECTED.value, 0)
        applied_count = status_dict.get(ApplicationStatus.APPLIED.value, 0)
        process_count = status_dict.get(ApplicationStatus.PROCESS.value, 0)
        interview_count = status_dict.get(ApplicationStatus.WAITING_DECISION.value, 0)
        offer_count = status_dict.get(ApplicationStatus.OFFER.value, 0)
        
        total_progressed = applied_count + interview_count + offer_count
        
        # Conversion rates
        collected_to_applied = (total_progressed / (collected_count + total_progressed) * 100) if (collected_count + total_progressed) > 0 else 0
        applied_to_process = ((process_count + offer_count + interview_count) / (applied_count + process_count + interview_count + offer_count) * 100) if (applied_count + process_count + interview_count + offer_count) > 0 else 0
        process_to_interview = ((interview_count + offer_count) / (process_count + interview_count + offer_count) * 100) if (process_count + interview_count + offer_count) > 0 else 0
        interview_to_offer = (offer_count / (interview_count + offer_count) * 100) if (interview_count + offer_count) > 0 else 0
        
        return {
            'status_distribution': status_dict,
            'conversion_rates': {
                'collected_to_applied': round(collected_to_applied, 1),
                'applied_to_process': round(applied_to_process, 1),
                'process_to_interview': round(process_to_interview, 1),
                'interview_to_offer': round(interview_to_offer, 1)
            }
        }
    
    @staticmethod
    def get_location_analytics():
        """Get location and work mode analytics"""
        # Remote work percentage
        total_jobs = JobApplication.query.count()
        remote_jobs = JobApplication.query.filter(
            JobApplication.job_mode == JobMode.REMOTE.value
        ).count()
        
        remote_percentage = (remote_jobs / total_jobs * 100) if total_jobs > 0 else 0
        
        # Country distribution
        country_counts = db.session.query(
            JobApplication.country,
            func.count(JobApplication.id).label('count')
        ).filter(
            JobApplication.country.isnot(None)
        ).group_by(JobApplication.country).order_by(
            func.count(JobApplication.id).desc()
        ).all()
        
        country_distribution = [
            {'country': country, 'count': count}
            for country, count in country_counts if country
        ]
        
        # Job mode distribution
        mode_counts = db.session.query(
            JobApplication.job_mode,
            func.count(JobApplication.id).label('count')
        ).group_by(JobApplication.job_mode).all()
        
        job_mode_distribution = {mode: count for mode, count in mode_counts}
        
        return {
            'remote_percentage': round(remote_percentage, 1),
            'country_distribution': country_distribution,
            'job_mode_distribution': job_mode_distribution
        }
    
    @staticmethod
    def get_trends_data():
        """Get trending data and month-over-month changes"""
        now = datetime.utcnow()
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        previous_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        
        # Current month applications
        current_month_applications = JobApplication.query.filter(
            JobApplication.last_update >= current_month_start
        ).count()
        
        # Previous month applications
        previous_month_applications = JobApplication.query.filter(
            and_(
                JobApplication.last_update >= previous_month_start,
                JobApplication.last_update < current_month_start
            )
        ).count()
        
        # Month over month change
        if previous_month_applications > 0:
            mom_change = ((current_month_applications - previous_month_applications) / previous_month_applications) * 100
        else:
            mom_change = 0 if current_month_applications == 0 else 100
        
        # Trending companies (companies with recent activity)
        trending_companies_data = db.session.query(
            JobApplication.company,
            func.count(JobApplication.id).label('recent_count')
        ).filter(
            JobApplication.last_update >= current_month_start
        ).group_by(JobApplication.company).having(
            func.count(JobApplication.id) >= 2
        ).order_by(func.count(JobApplication.id).desc()).limit(5).all()
        
        trending_companies = [
            {'company': company, 'trend': count * 10}  # Simple trend calculation
            for company, count in trending_companies_data
        ]
        
        return {
            'month_over_month_change': round(mom_change, 1),
            'current_month_applications': current_month_applications,
            'previous_month_applications': previous_month_applications,
            'trending_companies': trending_companies
        }
    
    @staticmethod
    def get_skill_analytics():
        """Get skill-related analytics"""        
        # Most required skills
        skill_counts = db.session.query(
            Skill.name,
            func.count(JobSkill.id).label('count')
        ).join(JobSkill, Skill.id == JobSkill.skill_id
        ).filter(Skill.is_blacklisted.is_(False)
        ).group_by(Skill.name).order_by(
            func.count(JobSkill.id).desc()
        ).limit(10).all()
        
        top_skills = [
            {'skill': skill, 'count': count}
            for skill, count in skill_counts
        ]
        
        # Skills by success rate
        skill_success_rates = db.session.query(
            Skill.name,
            func.count(JobSkill.id).label('total_jobs'),
            func.sum(
                case(
                    (JobApplication.status.in_([ApplicationStatus.OFFER.value, ApplicationStatus.WAITING_DECISION.value, ApplicationStatus.ACCEPTED.value]), 1),
                    else_=0
                )
            ).label('successful_jobs')
        ).join(JobSkill, Skill.id == JobSkill.skill_id
        ).join(JobApplication, JobSkill.job_id == JobApplication.id
        ).filter(Skill.is_blacklisted==False
        ).group_by(Skill.name).having(
            func.count(JobSkill.id) >= 3  # Only skills with at least 3 job applications
        ).all()
        
        skills_by_success = []
        for skill, total, successful in skill_success_rates:
            success_rate = (successful / total * 100) if total > 0 else 0
            skills_by_success.append({
                'skill': skill,
                'success_rate': round(success_rate, 1),
                'total_jobs': total
            })
        
        skills_by_success.sort(key=lambda x: x['success_rate'], reverse=True)
        
        return {
            'top_skills': top_skills,
            'skills_by_success': skills_by_success[:10]
        }
    
    @classmethod
    def get_all_analytics(cls):
        """Get all analytics data in one call"""
        return {
            'overview_stats': cls.get_overview_stats(),
            'performance_metrics': cls.get_performance_metrics(),
            'timeline_data': cls.get_timeline_data(),
            'company_analytics': cls.get_company_analytics(),
            'status_analytics': cls.get_status_analytics(),
            'location_analytics': cls.get_location_analytics(),
            'trends': cls.get_trends_data(),
            'skill_analytics': cls.get_skill_analytics()
        }

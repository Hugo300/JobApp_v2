"""
Comprehensive Skill Analytics Service

Provides detailed analytics for skills including:
- Usage statistics across job applications
- Trending skills analysis
- Skill performance metrics
- Market demand analysis
- User skill proficiency tracking
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
from collections import defaultdict, Counter
from sqlalchemy import func, desc, and_, or_
from models import db, JobApplication, CategoryItem, Category, CategoryType, ApplicationStatus
from services.skill_extraction_service import SkillExtractionService
from services.skill_matching_service import SkillMatchingService


class SkillAnalyticsService:
    """Service for comprehensive skill analytics and insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.skill_extraction = SkillExtractionService()
        self.skill_matching = SkillMatchingService()
    
    def get_skill_usage_statistics(self, days: int = 90) -> Dict[str, Any]:
        """Get comprehensive skill usage statistics"""
        try:
            cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
            
            # Get all job applications in the time period
            jobs = JobApplication.query.filter(
                JobApplication.last_update >= cutoff_date
            ).all()
            
            if not jobs:
                return {
                    'total_jobs': 0,
                    'skills_extracted': 0,
                    'top_skills': [],
                    'category_distribution': {},
                    'time_period': f'Last {days} days'
                }
            
            # Extract skills from all job descriptions
            all_skills = []
            skills_by_job = {}
            
            for job in jobs:
                if job.description:
                    extraction_result = self.skill_extraction.extract_skills(job.description)
                    if extraction_result['success']:
                        job_skills = extraction_result['skills']
                        all_skills.extend(job_skills)
                        skills_by_job[job.id] = job_skills
            
            # Count skill frequencies
            skill_counter = Counter(all_skills)
            
            # Get category distribution
            category_stats = self._get_category_distribution(all_skills)
            
            # Calculate top skills with additional metrics
            top_skills = []
            for skill, count in skill_counter.most_common(20):
                # Calculate job coverage (percentage of jobs that mention this skill)
                job_coverage = sum(1 for job_skills in skills_by_job.values() if skill in job_skills)
                coverage_percentage = (job_coverage / len(jobs)) * 100 if jobs else 0
                
                # Get category information
                category_info = self._get_skill_category(skill)
                
                top_skills.append({
                    'skill': skill,
                    'count': count,
                    'job_coverage': job_coverage,
                    'coverage_percentage': round(coverage_percentage, 1),
                    'category': category_info
                })
            
            return {
                'total_jobs': len(jobs),
                'skills_extracted': len(set(all_skills)),
                'total_skill_mentions': len(all_skills),
                'top_skills': top_skills,
                'category_distribution': category_stats,
                'time_period': f'Last {days} days',
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting skill usage statistics: {str(e)}")
            return {'error': str(e)}
    
    def get_trending_skills(self, current_days: int = 30, comparison_days: int = 60) -> Dict[str, Any]:
        """Analyze trending skills by comparing recent vs historical data"""
        try:
            now = datetime.now(timezone.utc)
            current_cutoff = now - timedelta(days=current_days)
            historical_cutoff = now - timedelta(days=comparison_days)
            
            # Get current period jobs
            current_jobs = JobApplication.query.filter(
                JobApplication.last_update >= current_cutoff
            ).all()

            # Get historical period jobs (excluding current period)
            historical_jobs = JobApplication.query.filter(
                and_(
                    JobApplication.last_update >= historical_cutoff,
                    JobApplication.last_update < current_cutoff
                )
            ).all()
            
            # Extract skills for both periods
            current_skills = self._extract_skills_from_jobs(current_jobs)
            historical_skills = self._extract_skills_from_jobs(historical_jobs)
            
            # Calculate frequencies
            current_counter = Counter(current_skills)
            historical_counter = Counter(historical_skills)
            
            # Calculate trends
            trending_skills = []
            all_skills = set(current_skills + historical_skills)
            
            for skill in all_skills:
                current_count = current_counter.get(skill, 0)
                historical_count = historical_counter.get(skill, 0)
                
                # Calculate trend metrics
                if historical_count > 0:
                    growth_rate = ((current_count - historical_count) / historical_count) * 100
                else:
                    growth_rate = 100 if current_count > 0 else 0
                
                # Only include skills with significant presence
                if current_count >= 2 or historical_count >= 2:
                    trending_skills.append({
                        'skill': skill,
                        'current_count': current_count,
                        'historical_count': historical_count,
                        'growth_rate': round(growth_rate, 1),
                        'trend': 'rising' if growth_rate > 20 else 'falling' if growth_rate < -20 else 'stable',
                        'category': self._get_skill_category(skill)
                    })
            
            # Sort by growth rate
            trending_skills.sort(key=lambda x: x['growth_rate'], reverse=True)
            
            return {
                'trending_up': [s for s in trending_skills if s['trend'] == 'rising'][:10],
                'trending_down': [s for s in trending_skills if s['trend'] == 'falling'][:10],
                'stable_skills': [s for s in trending_skills if s['trend'] == 'stable'][:10],
                'current_period': f'Last {current_days} days',
                'comparison_period': f'{comparison_days}-{current_days} days ago',
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing trending skills: {str(e)}")
            return {'error': str(e)}
    
    def get_skill_performance_metrics(self, user_skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get performance metrics for skills across job applications"""
        try:
            # Get all job applications
            jobs = JobApplication.query.all()
            
            if not jobs:
                return {'error': 'No job applications found'}
            
            # Group jobs by status
            status_groups = defaultdict(list)
            for job in jobs:
                status_groups[job.status].append(job)
            
            # Analyze skills by application outcome
            skill_performance = defaultdict(lambda: {
                'total_applications': 0,
                'successful_applications': 0,  # Applied, Interview, Offer, Accepted
                'rejected_applications': 0,
                'pending_applications': 0,
                'success_rate': 0.0
            })
            
            successful_statuses = [
                ApplicationStatus.APPLIED.value,
                ApplicationStatus.INTERVIEW.value,
                ApplicationStatus.OFFER.value,
                ApplicationStatus.ACCEPTED.value
            ]
            
            for job in jobs:
                if job.description:
                    extraction_result = self.skill_extraction.extract_skills(job.description)
                    if extraction_result['success']:
                        job_skills = extraction_result['skills']
                        
                        for skill in job_skills:
                            skill_performance[skill]['total_applications'] += 1
                            
                            if job.status in successful_statuses:
                                skill_performance[skill]['successful_applications'] += 1
                            elif job.status == ApplicationStatus.REJECTED.value:
                                skill_performance[skill]['rejected_applications'] += 1
                            else:
                                skill_performance[skill]['pending_applications'] += 1
            
            # Calculate success rates
            performance_list = []
            for skill, metrics in skill_performance.items():
                if metrics['total_applications'] >= 3:  # Only include skills with sufficient data
                    success_rate = (metrics['successful_applications'] / metrics['total_applications']) * 100
                    metrics['success_rate'] = round(success_rate, 1)
                    
                    performance_list.append({
                        'skill': skill,
                        'category': self._get_skill_category(skill),
                        **metrics
                    })
            
            # Sort by success rate
            performance_list.sort(key=lambda x: x['success_rate'], reverse=True)
            
            return {
                'top_performing_skills': performance_list[:15],
                'underperforming_skills': performance_list[-10:] if len(performance_list) > 10 else [],
                'total_skills_analyzed': len(performance_list),
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting skill performance metrics: {str(e)}")
            return {'error': str(e)}
    
    def _extract_skills_from_jobs(self, jobs: List[JobApplication]) -> List[str]:
        """Extract skills from a list of job applications"""
        all_skills = []
        for job in jobs:
            if job.description:
                extraction_result = self.skill_extraction.extract_skills(job.description)
                if extraction_result['success']:
                    all_skills.extend(extraction_result['skills'])
        return all_skills
    
    def _get_category_distribution(self, skills: List[str]) -> Dict[str, Any]:
        """Get distribution of skills across categories"""
        try:
            category_counts = defaultdict(int)
            uncategorized_count = 0
            
            for skill in skills:
                category_info = self._get_skill_category(skill)
                if category_info:
                    category_counts[category_info['name']] += 1
                else:
                    uncategorized_count += 1
            
            total_skills = len(skills)
            distribution = {}
            
            for category, count in category_counts.items():
                percentage = (count / total_skills) * 100 if total_skills > 0 else 0
                distribution[category] = {
                    'count': count,
                    'percentage': round(percentage, 1)
                }
            
            if uncategorized_count > 0:
                percentage = (uncategorized_count / total_skills) * 100
                distribution['Uncategorized'] = {
                    'count': uncategorized_count,
                    'percentage': round(percentage, 1)
                }
            
            return distribution
            
        except Exception as e:
            self.logger.error(f"Error getting category distribution: {str(e)}")
            return {}
    
    def _get_skill_category(self, skill: str) -> Optional[Dict[str, str]]:
        """Get category information for a skill"""
        try:
            skill_lower = skill.lower().strip()
            
            # Find category item that matches this skill
            categories = Category.query.filter_by(category_type=CategoryType.SKILL.value).all()
            
            for category in categories:
                items = CategoryItem.query.filter_by(category_id=category.id, is_active=True).all()
                
                for item in items:
                    # Check direct name match
                    if item.normalized_name == skill_lower:
                        return {
                            'id': category.id,
                            'name': category.name,
                            'color': category.color,
                            'icon': category.icon
                        }
                    
                    # Check keyword matches
                    keywords = item.get_keywords_list()
                    for keyword in keywords:
                        if keyword.lower() in skill_lower or skill_lower in keyword.lower():
                            return {
                                'id': category.id,
                                'name': category.name,
                                'color': category.color,
                                'icon': category.icon
                            }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error getting skill category: {str(e)}")
            return None

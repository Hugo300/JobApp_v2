"""
Job service for handling job application business logic
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import joinedload

from models import JobApplication, JobSkill, ApplicationStatus, JobMode, db, Skill

from .base_service import BaseService
from .skill_service import SkillService

from utils.scraper import scrape_job_details
from utils.responses import handle_scraping_response
from utils.forms import sanitize_input


class JobService(BaseService):
    """Service for job application operations"""

    def __init__(self):
        super().__init__()
        self.skill_service = SkillService()

    def get_job_by_id(self, job_id):
        """Get job application by ID"""
        return self.get_by_id(JobApplication, job_id)
    
    def get_all_jobs(self, order_by=None, include_relationships=False):
        """
        Get all job applications with optimized queries

        Args:
            order_by: Order by clause
            include_relationships: Whether to eagerly load relationships

        Returns:
            List[JobApplication]: List of job applications
        """
        try:
            query = JobApplication.query

            # Eagerly load relationships to prevent N+1 queries
            if include_relationships:
                from sqlalchemy.orm import joinedload
                query = query.options(
                    joinedload(JobApplication.documents),
                    joinedload(JobApplication.logs)
                )

            if order_by is None:
                query = query.order_by(JobApplication.last_update.desc())
            else:
                query = query.order_by(order_by)

            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting all jobs: {str(e)}")
            return []

    def get_jobs_paginated(self, page=1, per_page=20, search_query=None, status_filter=None,
                          job_mode_filter=None, country_filter=None):
        """
        Get paginated job applications with filtering

        Args:
            page: Page number
            per_page: Items per page
            search_query: Search term
            status_filter: Status filter
            job_mode_filter: Job mode filter
            country_filter: Country filter

        Returns:
            Pagination object with optimized queries
        """
        try:
            from sqlalchemy.orm import joinedload

            query = JobApplication.query.options(
                joinedload(JobApplication.documents),
                joinedload(JobApplication.logs).limit(5)  # Only load recent logs
            )

            # Apply filters
            if search_query:
                search_term = f"%{search_query}%"
                query = query.filter(
                    db.or_(
                        JobApplication.company.ilike(search_term),
                        JobApplication.title.ilike(search_term),
                        JobApplication.description.ilike(search_term)
                    )
                )

            if status_filter:
                query = query.filter(JobApplication.status == status_filter)

            if job_mode_filter:
                query = query.filter(JobApplication.job_mode == job_mode_filter)

            if country_filter:
                query = query.filter(JobApplication.country == country_filter)

            # Order by last update
            query = query.order_by(JobApplication.last_update.desc())

            return query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )

        except Exception as e:
            self.logger.error(f"Error getting paginated jobs: {str(e)}")
            # Return empty pagination object
            from flask_sqlalchemy import Pagination
            return Pagination(query=None, page=page, per_page=per_page, total=0, items=[])
    
    def create_job(self, company, title, description=None, url=None,
                   office_location=None, country=None, job_mode=None):
        """
        Create a new job application

        Args:
            company: Company name
            title: Job title
            description: Job description
            url: Job posting URL
            office_location: Office location
            country: Country
            job_mode: Job mode (remote, hybrid, on-site)

        Returns:
            tuple: (success: bool, job: JobApplication, error: str)
        """
        # Validate and sanitize inputs
        try:
            if not company or not company.strip():
                return False, None, "Company name is required"

            if not title or not title.strip():
                return False, None, "Job title is required"

            # Sanitize all string inputs
            company = sanitize_input(company)
            title = sanitize_input(title)
            description = sanitize_input(description) if description else None
            url = sanitize_input(url) if url else None
            office_location = sanitize_input(office_location) if office_location else None
            country = sanitize_input(country) if country else None

            # Validate job mode
            if job_mode and job_mode not in [mode.value for mode in JobMode]:
                job_mode = JobMode.ON_SITE.value

        except Exception as e:
            self.logger.error(f"Error validating job data: {str(e)}")
            return False, None, f"Validation error: {str(e)}"

        job_data = {
            'company': company,
            'title': title,
            'description': description,
            'url': url,
            'office_location': office_location,
            'country': country,
            'job_mode': job_mode or JobMode.ON_SITE.value,
            'status': ApplicationStatus.COLLECTED.value,
            'last_update': datetime.now(timezone.utc)
        }

        # Create the job
        success, job, error = self.create(JobApplication, **job_data)

        if success:
            # extract the skills from the text
            success, _ = self.extract_job_skills(job.id, job_data['description'])

        return success, job, error
    
    def update_job(self, job_id, **kwargs):
        """
        Update a job application

        Args:
            job_id: Job ID
            **kwargs: Fields to update

        Returns:
            tuple: (success: bool, job: JobApplication, error: str)
        """
        job = self.get_job_by_id(job_id)
        if not job:
            return False, None, "Job not found"

        # Update last_update timestamp
        kwargs['last_update'] = datetime.now(timezone.utc)

        # Update the job
        success, updated_job, error = self.update(job, **kwargs)

        return success, updated_job, error
    
    def delete_job(self, job_id):
        """
        Delete a job application and all associated data
        
        Args:
            job_id: Job ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        job = self.get_job_by_id(job_id)
        if not job:
            return False, None, "Job not found"
        
        def _delete_job():
            # Delete associated logs
            from models import JobLog
            JobLog.query.filter_by(job_id=job_id).delete()
            
            # Delete the job
            db.session.delete(job)
            return True
        
        return self.safe_execute(_delete_job)
    
    def filter_jobs(self, search_query=None, status_filter=None, 
                   job_mode_filter=None, country_filter=None):
        """
        Filter job applications based on criteria
        
        Args:
            search_query: Text to search in company, title, description
            status_filter: Filter by application status
            job_mode_filter: Filter by job mode
            country_filter: Filter by country
            
        Returns:
            List of filtered job applications
        """
        try:
            query = JobApplication.query
            
            # Apply search filter
            if search_query and search_query.strip():
                search_pattern = f'%{search_query.strip()}%'
                query = query.filter(
                    db.or_(
                        JobApplication.company.ilike(search_pattern),
                        JobApplication.title.ilike(search_pattern),
                        JobApplication.description.ilike(search_pattern)
                    )
                )
            
            # Apply status filter
            if status_filter and status_filter.strip():
                query = query.filter(JobApplication.status == status_filter.strip())
            
            # Apply job mode filter
            if job_mode_filter and job_mode_filter.strip():
                query = query.filter(JobApplication.job_mode == job_mode_filter.strip())
            
            # Apply country filter
            if country_filter and country_filter.strip():
                query = query.filter(JobApplication.country == country_filter.strip())
            
            return query.order_by(JobApplication.last_update.desc()).all()
            
        except Exception as e:
            self.logger.error(f"Error filtering jobs: {str(e)}")
            return []
    
    def get_job_statistics(self):
        """
        Get job application statistics
        
        Returns:
            dict: Statistics including counts, percentages, and top countries
        """
        try:
            all_jobs = self.get_all_jobs()
            total_jobs = len(all_jobs)
            
            if total_jobs == 0:
                return {
                    'total_jobs': 0,
                    'status_counts': {},
                    'status_percentages': {},
                    'job_mode_counts': {},
                    'country_counts': {},
                    'top_countries': []
                }
            
            status_counts = {}
            job_mode_counts = {}
            country_counts = {}
            
            for job in all_jobs:
                # Count by status
                status = job.status
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by job mode
                if job.job_mode:
                    job_mode_counts[job.job_mode] = job_mode_counts.get(job.job_mode, 0) + 1
                
                # Count by country
                if job.country:
                    country_counts[job.country] = country_counts.get(job.country, 0) + 1
            
            # Calculate percentages for status
            status_percentages = {}
            for status, count in status_counts.items():
                status_percentages[status] = round((count / total_jobs) * 100, 1)
            
            return {
                'total_jobs': total_jobs,
                'status_counts': status_counts,
                'status_percentages': status_percentages,
                'job_mode_counts': job_mode_counts,
                'country_counts': country_counts,
                'top_countries': sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating job statistics: {str(e)}")
            return {
                'total_jobs': 0,
                'status_counts': {},
                'status_percentages': {},
                'job_mode_counts': {},
                'country_counts': {},
                'top_countries': []
            }
    
    def scrape_job_details(self, url):
        """
        Scrape job details from URL
        
        Args:
            url: Job posting URL
            
        Returns:
            dict: Scraped job details
        """
        try:
            result = scrape_job_details(url)
            return handle_scraping_response(result)
        except Exception as e:
            self.logger.error(f"Error scraping job details: {str(e)}")
            return {
                'success': False,
                'error': 'Failed to scrape job details'
            }

    
    def update_job_status(self, job_id, new_status):
        """
        Update job application status
        
        Args:
            job_id: Job ID
            new_status: New status value
            
        Returns:
            tuple: (success: bool, job: JobApplication, error: str)
        """
        # Validate status
        valid_statuses = [status.value for status in ApplicationStatus]
        if new_status not in valid_statuses:
            return False, None, "Invalid status"
        
        return self.update_job(job_id, status=new_status)
    
    def extract_job_skills(self, job_id, job_description):
        """
        Extract skills from the job description and store them in the JobSkill table.

        :param job_id: ID of the job
        :param job_description: Description of the job
        """
        # Extract skills
        extracted_skills = self.skill_service.extract_skills(job_description)

        # Fetch or create skills in the database
        skill_ids = []
        for skill_name in extracted_skills['skills']:
            skill = db.session.query(Skill).filter_by(name=skill_name).first()

            # if skill does not exist then add it to the db
            if not skill:
                _, skill, _ = self.skill_service.create_skill(name=skill_name)

            skill_ids.append(skill.id)

        # Link skills to the job
        for skill_id in skill_ids:
            self.create(JobSkill, **{
                'job_id': job_id,
                'skill_id': skill_id
            })

        return True, extracted_skills

    def get_job_skills(self, job_id):
        query = JobApplication.query

        job = query.filter(JobApplication.id == job_id).first()

        skills = list(job.skills)

        return skills
    
    def get_job_skills_by_category(self, job_id, get_blacklisted=False):
        job = JobApplication.query.filter(JobApplication.id == job_id).first()

        if not job:
            return {}

        skills_by_category = defaultdict(list)

        # Use your association proxy to get skills directly
        for skill in job.skills:  # Using your Job -> Skill association proxy
            category = skill.skill_category

            category_name = "Uncategorized" if not category else category.name

            if get_blacklisted:
                skills_by_category[category_name].append(skill.name)
            elif not skill.is_blacklisted:  # Fixed condition
                skills_by_category[category_name].append(skill.name)

        return dict(skills_by_category)
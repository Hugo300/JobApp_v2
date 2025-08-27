"""
Job service for handling job application business logic
"""
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from collections import defaultdict
from sqlalchemy.orm import joinedload
from flask_sqlalchemy.pagination import Pagination
import logging

from models import JobApplication, JobSkill, ApplicationStatus, JobMode, JobLog, db, Skill

from .base_service import BaseService
from .skill.skill_service import get_skill_service

from utils.scraper import scrape_job_data
from utils.responses import handle_scraping_response
from utils.forms import sanitize_input

# Configure module logger
logger = logging.getLogger(__name__)

class JobService(BaseService):
    """Service for job application operations"""

    def __init__(self):
        super().__init__()
        # Get the skill service instance
        self.skill_service = get_skill_service()
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.logger.info("JobService initialized")

    def get_job_by_id(self, job_id):
        """Get job application by ID"""
        try:
            self.logger.debug(f"Fetching job by ID: {job_id}")
            job = self.get_by_id(JobApplication, job_id)
            
            if job:
                self.logger.debug(f"Job found: {job.company} - {job.title}")
            else:
                self.logger.warning(f"Job not found with ID: {job_id}")
            
            return job
        except Exception as e:
            self.logger.error(f"Error fetching job by ID {job_id}: {str(e)}", exc_info=True)
            return None
    
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
            self.logger.debug(f"Fetching all jobs (include_relationships: {include_relationships})")
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

            jobs = query.all()
            self.logger.info(f"Retrieved {len(jobs)} job applications")
            return jobs
        except Exception as e:
            self.logger.error(f"Error getting all jobs: {str(e)}", exc_info=True)
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
            self.logger.debug(f"Fetching paginated jobs - Page: {page}, Per page: {per_page}")
            self.logger.debug(f"Filters - Search: {search_query}, Status: {status_filter}, "
                            f"Mode: {job_mode_filter}, Country: {country_filter}")

            query = JobApplication.query.options(
                joinedload(JobApplication.documents),
                joinedload(JobApplication.logs).limit(5)  # Only load recent logs
            )

            # Apply filters
            filters_applied = []

            if search_query:
                search_term = f"%{search_query}%"
                query = query.filter(
                    db.or_(
                        JobApplication.company.ilike(search_term),
                        JobApplication.title.ilike(search_term),
                        JobApplication.description.ilike(search_term)
                    )
                )
                filters_applied.append(f"search='{search_query}'")

            if status_filter:
                query = query.filter(JobApplication.status == status_filter)
                filters_applied.append(f"status='{status_filter}'")

            if job_mode_filter:
                query = query.filter(JobApplication.job_mode == job_mode_filter)
                filters_applied.append(f"mode='{job_mode_filter}'")

            if country_filter:
                query = query.filter(JobApplication.country == country_filter)
                filters_applied.append(f"country='{country_filter}'")

            if filters_applied:
                self.logger.debug(f"Applied filters: {', '.join(filters_applied)}")

            # Order by last update
            query = query.order_by(JobApplication.last_update.desc())

            pagination = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
        
            self.logger.info(f"Paginated query returned {pagination.total} total jobs, "
                           f"showing {len(pagination.items)} items on page {page}")
            
            return pagination

        except Exception as e:
            self.logger.error(f"Error getting paginated jobs: {str(e)}", exc_info=True)
            # Return empty pagination object
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
        self.logger.info(f"Creating new job application: {company} - {title}")

        # Validate and sanitize inputs
        try:
            if not company or not company.strip():
                self.logger.warning("Job creation failed: Company name is required")
                return False, None, "Company name is required"

            if not title or not title.strip():
                self.logger.warning("Job creation failed: Job title is required")
                return False, None, "Job title is required"

            # Sanitize all string inputs
            company = sanitize_input(company)
            title = sanitize_input(title)
            description = sanitize_input(description) if description else None
            url = sanitize_input(url) if url else None
            office_location = sanitize_input(office_location) if office_location else None
            country = sanitize_input(country) if country else None

            self.logger.debug(f"Input sanitization completed for job: {company} - {title}")

            # Validate job mode
            if job_mode and job_mode not in [mode.value for mode in JobMode]:
                self.logger.warning(f"Invalid job mode '{job_mode}' provided, defaulting to ON_SITE")
                job_mode = JobMode.ON_SITE.value

        except Exception as e:
            self.logger.error(f"Error validating job data for {company} - {title}: {str(e)}", exc_info=True)
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
            self.logger.info(f"Job application created successfully: ID={job.id}, {company} - {title}")
            
            # Extract skills from the description
            if description:
                self.logger.debug(f"Extracting skills from job description for job ID: {job.id}")
                skill_success, skills = self.extract_job_skills(job.id, job_data['description'])

                if skill_success:
                    self.logger.info(f"Skills extracted successfully for job {job.id}: {len(skills)} skills found")
                else:
                    self.logger.warning(f"Skill extraction failed for job {job.id}")
            else:
                self.logger.debug(f"No description provided for job {job.id}, skipping skill extraction")
        else:
            self.logger.error(f"Failed to create job application for {company} - {title}: {error}")

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
        self.logger.info(f"Updating job application ID: {job_id}")
        self.logger.debug(f"Update fields: {list(kwargs.keys())}")

        job = self.get_job_by_id(job_id)
        if not job:
            self.logger.warning(f"Update failed: Job not found with ID: {job_id}")
            return False, None, "Job not found"
        
        # Log what's being updated
        updated_fields = []
        for key, value in kwargs.items():
            if hasattr(job, key) and getattr(job, key) != value:
                old_value = getattr(job, key)
                updated_fields.append(f"{key}: '{old_value}' -> '{value}'")

        # Update last_update timestamp
        kwargs['last_update'] = datetime.now(timezone.utc)

        # Update the job
        success, updated_job, error = self.update(job, **kwargs)

        if success:
            self.logger.info(f"Job {job_id} updated successfully")
            if updated_fields:
                self.logger.debug(f"Changed fields: {', '.join(updated_fields)}")
        else:
            self.logger.error(f"Failed to update job {job_id}: {error}")

        return success, updated_job, error
    
    def delete_job(self, job_id):
        """
        Delete a job application and all associated data
        
        Args:
            job_id: Job ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        self.logger.info(f"Deleting job application ID: {job_id}")

        job = self.get_job_by_id(job_id)
        if not job:
            self.logger.warning(f"Delete failed: Job not found with ID: {job_id}")
            return False, None, "Job not found"
        
        # Log job details before deletion
        self.logger.info(f"Deleting job: {job.company} - {job.title} (Status: {job.status})")
        
        def _delete_job():
            # Delete associated logs
            log_count = JobLog.query.filter_by(job_id=job_id).count()
            JobLog.query.filter_by(job_id=job_id).delete()
            self.logger.debug(f"Deleted {log_count} associated job logs")
            
            # Delete the job
            db.session.delete(job)
            self.logger.debug(f"Job {job_id} marked for deletion")
            return True
        
        success, result, error = self.safe_execute(_delete_job)
        
        if success:
            self.logger.info(f"Job {job_id} deleted successfully")
        else:
            self.logger.error(f"Failed to delete job {job_id}: {error}")
            
        return success, result, error
    
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
            self.logger.debug("Filtering jobs with criteria")
            filters = []
            if search_query: filters.append(f"search='{search_query}'")
            if status_filter: filters.append(f"status='{status_filter}'")
            if job_mode_filter: filters.append(f"mode='{job_mode_filter}'")
            if country_filter: filters.append(f"country='{country_filter}'")

            if filters:
                self.logger.debug(f"Applied filters: {', '.join(filters)}")
            
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
            
            jobs = query.order_by(JobApplication.last_update.desc()).all()
            self.logger.info(f"Filter returned {len(jobs)} job applications")
            return jobs
            
        except Exception as e:
            self.logger.error(f"Error filtering jobs: {str(e)}", exc_info=True)
            return []
    
    def get_job_statistics(self):
        """
        Get job application statistics
        
        Returns:
            dict: Statistics including counts, percentages, and top countries
        """
        try:
            self.logger.debug("Calculating job statistics")
            all_jobs = self.get_all_jobs()
            total_jobs = len(all_jobs)
            
            if total_jobs == 0:
                self.logger.info("No jobs found for statistics calculation")
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
            
            stats = {
                'total_jobs': total_jobs,
                'status_counts': status_counts,
                'status_percentages': status_percentages,
                'job_mode_counts': job_mode_counts,
                'country_counts': country_counts,
                'top_countries': sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            }
        
            self.logger.info(f"Statistics calculated for {total_jobs} jobs: "
                           f"{len(status_counts)} statuses, {len(country_counts)} countries")
            self.logger.debug(f"Status distribution: {status_counts}")

            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculating job statistics: {str(e)}", exc_info=True)
            return {
                'total_jobs': 0,
                'status_counts': {},
                'status_percentages': {},
                'job_mode_counts': {},
                'country_counts': {},
                'top_countries': []
            }
    
    def scrape_job_data(self, url):
        """
        Scrape job details from URL
        
        Args:
            url: Job posting URL
            
        Returns:
            dict: Scraped job details
        """
        self.logger.info(f"Scraping job data from URL: {url}")

        try:
            result = scrape_job_data(url)
            response = handle_scraping_response(result)
        
            if response.get('success'):
                self.logger.info(f"Job data scraped successfully from {url}")
                self.logger.debug(f"Scraped data keys: {list(response.get('data', {}).keys())}")
            else:
                self.logger.warning(f"Job scraping failed for {url}: {response.get('error', 'Unknown error')}")
        
        except Exception as e:
            self.logger.error(f"Error scraping job data from {url}: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to scrape job data. More info: {str(e)}'
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
        self.logger.info(f"Updating status for job {job_id} to '{new_status}'")

        # Validate status
        valid_statuses = [status.value for status in ApplicationStatus]
        if new_status not in valid_statuses:
            self.logger.warning(f"Invalid status '{new_status}' provided for job {job_id}. "
                              f"Valid statuses: {valid_statuses}")
            return False, None, "Invalid status"
        
        # Get current job for logging
        job = self.get_job_by_id(job_id)
        if job:
            old_status = job.status
            self.logger.debug(f"Status change for job {job_id}: '{old_status}' -> '{new_status}'")
        
        success, updated_job, error = self.update_job(job_id, status=new_status)
        
        if success:
            self.logger.info(f"Status updated successfully for job {job_id}")
        else:
            self.logger.error(f"Failed to update status for job {job_id}: {error}")
            
        return success, updated_job, error
    
    def create_job_skill(self, job_id, skill_id):
        """Create a job-skill relationship"""
        self.logger.debug(f"Creating job-skill relationship: job_id={job_id}, skill_id={skill_id}")

        # check if relation exists
        job_skill = JobSkill.query.filter_by(job_id=job_id, skill_id=skill_id).first()

        # create relation if it does not exist
        if job_skill is None:  # Use 'is' for None comparison
            success, job_skill, error = self.create(JobSkill, **{
                'job_id': job_id,
                'skill_id': skill_id
            })
            
            if success:
                self.logger.debug(f"Job-skill relationship created: job_id={job_id}, skill_id={skill_id}")
            else:
                self.logger.error(f"Failed to create job-skill relationship: {error}")
                
            return success, job_skill, error
        else:
            self.logger.debug(f"Job-skill relationship already exists: job_id={job_id}, skill_id={skill_id}")
            
        return True, job_skill, None

    def extract_job_skills(self, job_id, job_description):
        """
        Extract skills from the job description and store them in the JobSkill table.

        :param job_id: ID of the job
        :param job_description: Description of the job
        """
        if not job_description:
            self.logger.debug(f"No job description provided for job {job_id}, skipping skill extraction")
            return True, []
        
        self.logger.info(f"Extracting skills from job description for job ID: {job_id}")

        try:
            # Extract skills
            extraction_result = self.skill_service.process_job_description(job_description)

            if extraction_result.success:
                skill_ids = []
                matched_skills = []

                for skill in extraction_result.normalized_skills:
                    skill_ids.append(skill.id)
                    matched_skills.append(skill.name)

                self.logger.debug(f"Matched skills for job {job_id}: {matched_skills}")

                # create skills that do not yet exist
                new_skills = []
                for skill_name in extraction_result.unmatched_skills:
                    skill = self.skill_service.create_skill(skill_name)
                    skill_ids.append(skill.id)
                    new_skills.append(skill_name)

                if new_skills:
                    self.logger.info(f"Created new skills for job {job_id}: {new_skills}")

                # Link skills to the job
                linked_skills = 0
                for skill_id in skill_ids:
                    success, _, error = self.create_job_skill(job_id, skill_id)
                    if success:
                        linked_skills += 1
                    else:
                        self.logger.warning(f"Failed to link skill {skill_id} to job {job_id}: {error}")
                
                self.logger.info(f"Skill extraction completed for job {job_id}: "
                               f"{len(matched_skills)} matched, {len(new_skills)} created, "
                               f"{linked_skills} linked")

                return True, extraction_result.normalized_skills
            else:
                self.logger.warning(f"Skill extraction failed for job {job_id}: "
                                  f"{getattr(extraction_result, 'error', 'Unknown error')}")
                return False, None
        
        except Exception as e:
            self.logger.error(f"Error extracting skills for job {job_id}: {str(e)}", exc_info=True)
            return False, None

    def get_job_skills(self, job_id):
        """Get skills for a specific job"""
        self.logger.debug(f"Fetching skills for job ID: {job_id}")

        try:
            query = JobApplication.query

            job = query.filter(JobApplication.id == job_id).first()

            if not job:
                self.logger.warning(f"Job not found when fetching skills: {job_id}")
                return []

            skills = list(job.skills)
            self.logger.debug(f"Retrieved {len(skills)} skills for job {job_id}")

            return skills
        except Exception as e:
            self.logger.error(f"Error fetching skills for job {job_id}: {str(e)}", exc_info=True)
            return []
    
    def get_job_skills_by_category(self, job_id, get_blacklisted=False):
        """Get job skills organized by category"""
        self.logger.debug(f"Fetching categorized skills for job ID: {job_id} "
                        f"(include_blacklisted: {get_blacklisted})")
        
        try:
            job = JobApplication.query.filter(JobApplication.id == job_id).first()

            if not job:
                    self.logger.warning(f"Job not found when fetching categorized skills: {job_id}")
                    return {}

            skills_by_category = defaultdict(list)
            total_skills = 0
            blacklisted_count = 0

            # Use your association proxy to get skills directly
            for skill in job.skills:  # Using your Job -> Skill association proxy
                total_skills += 1
                category = skill.category

                category_name = "Uncategorized" if not category else category.name

                if skill.is_blacklisted:
                    blacklisted_count += 1

                if get_blacklisted:
                    skills_by_category[category_name].append(skill.name)
                elif not skill.is_blacklisted:  # Fixed condition
                    skills_by_category[category_name].append(skill.name)

            result = {
                'total_skills': len(job.skills),
                'skills': dict(skills_by_category)
            }
        
            self.logger.info(f"Categorized skills for job {job_id}: {total_skills} total skills, "
                           f"{blacklisted_count} blacklisted, {len(skills_by_category)} categories")
            
            if self.logger.isEnabledFor(logging.DEBUG):
                for category, skills in skills_by_category.items():
                    self.logger.debug(f"Category '{category}': {len(skills)} skills")

            return result
        except Exception as e:
            self.logger.error(f"Error fetching categorized skills for job {job_id}: {str(e)}", exc_info=True)
            return {}
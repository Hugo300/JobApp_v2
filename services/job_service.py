"""
Job service for handling job application business logic
"""
from datetime import datetime
from models import JobApplication, ApplicationStatus, JobMode, db
from .base_service import BaseService
from utils.analysis import analyze_job_match
from utils.scraper import scrape_job_details
from utils.responses import handle_scraping_response, handle_job_match_response


class JobService(BaseService):
    """Service for job application operations"""
    
    def get_job_by_id(self, job_id):
        """Get job application by ID"""
        return self.get_by_id(JobApplication, job_id)
    
    def get_all_jobs(self, order_by=None):
        """Get all job applications"""
        try:
            query = JobApplication.query
            if order_by is None:
                query = query.order_by(JobApplication.last_update.desc())
            else:
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting all jobs: {str(e)}")
            return []
    
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
        job_data = {
            'company': company,
            'title': title,
            'description': description,
            'url': url,
            'office_location': office_location,
            'country': country,
            'job_mode': job_mode,
            'status': ApplicationStatus.COLLECTED.value,
            'created_at': datetime.utcnow(),
            'last_update': datetime.utcnow()
        }
        
        return self.create(JobApplication, **job_data)
    
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
        kwargs['last_update'] = datetime.utcnow()
        
        return self.update(job, **kwargs)
    
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
    
    def analyze_job_match(self, job_id, user_skills):
        """
        Analyze job match against user skills
        
        Args:
            job_id: Job ID
            user_skills: User skills string
            
        Returns:
            dict: Match analysis results
        """
        try:
            job = self.get_job_by_id(job_id)
            if not job:
                return {'match_score': 0, 'matched_keywords': [], 'unmatched_keywords': []}
            
            result = analyze_job_match(job.description or '', user_skills or '')
            return handle_job_match_response(result)
        except Exception as e:
            self.logger.error(f"Error analyzing job match: {str(e)}")
            return {'match_score': 0, 'matched_keywords': [], 'unmatched_keywords': []}
    
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

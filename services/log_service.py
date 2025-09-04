"""
Log service for handling job log business logic
"""
from datetime import datetime, timezone
from models import JobLog, JobApplication, ApplicationStatus, db
from .base_service import BaseService


class LogService(BaseService):
    """Service for job log operations"""
    
    def get_logs_for_job(self, job_id, order_by=None):
        """
        Get all logs for a specific job

        Args:
            job_id: Job ID
            order_by: Optional ordering column

        Returns:
            List of JobLog instances
        """
        try:
            query = JobLog.query.filter_by(job_id=job_id)
            if order_by is None:
                query = query.order_by(JobLog.created_at.desc())
            else:
                query = query.order_by(order_by)
            return query.all()
        except Exception as e:
            self.logger.error(f"Error getting logs for job {job_id}: {str(e)}")
            return []
    
    def get_log_by_id(self, log_id):
        """Get log entry by ID"""
        return self.get_by_id(JobLog, log_id)
    
    def create_log(self, job_id, note, status_change=None):
        """
        Create a new job log entry
        
        Args:
            job_id: ID of the job application
            note: Log note content
            status_change: Optional status change
            user_id: Optional user ID (for future multi-user support)
            
        Returns:
            tuple: (success: bool, log: JobLog, error: str)
        """
        # Verify job exists
        job = db.session.get(JobApplication, job_id)
        if not job:
            return False, None, "Job not found"
        
        def _create_log():
            log_data = {
                'job_id': job_id,
                'note': note,
                'created_at': datetime.now(timezone.utc)
            }
            
            # Handle status change
            if status_change:
                # Validate status
                valid_statuses = [status.value for status in ApplicationStatus]
                if status_change not in valid_statuses:
                    raise ValueError("Invalid status")
                
                old_status = job.status
                job.status = status_change
                job.last_update = datetime.now(timezone.utc)

                # Update log data to include status change
                log_data['status_change_from'] = old_status
                log_data['status_change_to'] = status_change
                log_data['note'] = f"Status changed from {old_status} to {status_change}. {note}"
            
            log = JobLog(**log_data)
            db.session.add(log)
            return log
        
        return self.safe_execute(_create_log)

    def update_log(self, log_id, note, status_change=None, job_id=None):
        """
        Update an existing log entry

        Args:
            log_id: ID of the log entry to update
            note: New note content

        Returns:
            tuple: (success: bool, log: JobLog, error: str)
        """
        log = self.get_log_by_id(log_id)
        if not log:
            return False, None, "Log entry not found"
        
        data = {'note': note}
        
        # Handle status change
        if status_change:
            # Validate status
            valid_statuses = [status.value for status in ApplicationStatus]
            if status_change not in valid_statuses:
                raise ValueError("Invalid status")
            
            job = db.session.get(JobApplication, job_id)
            if not job:
                return False, None, "Job not found"
            
            old_status = job.status
            job.status = status_change
            job.last_update = datetime.now(timezone.utc)

            # Update log data to include status change
            data['status_change_from'] = old_status
            data['status_change_to'] = status_change
        
        data['updated_at'] = datetime.now(timezone.utc)
        
        return self.update(log, **data)
    
    def delete_log(self, log_id):
        """
        Delete a log entry
        
        Args:
            log_id: Log ID
            
        Returns:
            tuple: (success: bool, result: bool, error: str)
        """
        log = self.get_log_by_id(log_id)
        if not log:
            return False, None, "Log not found"
        
        return self.delete(log)
    
    def get_recent_logs(self, limit=10):
        """
        Get recent log entries across all jobs
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            List of JobLog instances with job information
        """
        try:
            logs = JobLog.query.join(JobApplication).order_by(
                JobLog.created_at.desc()
            ).limit(limit).all()
            return logs
        except Exception as e:
            self.logger.error(f"Error getting recent logs: {str(e)}")
            return []
    
    def get_logs_by_date_range(self, start_date, end_date, job_id=None):
        """
        Get logs within a date range
        
        Args:
            start_date: Start date
            end_date: End date
            job_id: Optional job ID filter
            
        Returns:
            List of JobLog instances
        """
        try:
            query = JobLog.query.filter(
                JobLog.created_at >= start_date,
                JobLog.created_at <= end_date
            )
            
            if job_id:
                query = query.filter(JobLog.job_id == job_id)
            
            return query.order_by(JobLog.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting logs by date range: {str(e)}")
            return []
    
    def get_status_change_logs(self, job_id=None):
        """
        Get logs that contain status changes
        
        Args:
            job_id: Optional job ID filter
            
        Returns:
            List of JobLog instances that contain status changes
        """
        try:
            query = JobLog.query.filter(
                JobLog.note.like('%Status changed from%')
            )
            
            if job_id:
                query = query.filter(JobLog.job_id == job_id)
            
            return query.order_by(JobLog.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Error getting status change logs: {str(e)}")
            return []
    
    def get_log_statistics(self, job_id=None):
        """
        Get log statistics
        
        Args:
            job_id: Optional job ID filter
            
        Returns:
            dict: Log statistics
        """
        try:
            query = JobLog.query
            if job_id:
                query = query.filter(JobLog.job_id == job_id)
            
            total_logs = query.count()
            status_change_logs = query.filter(
                JobLog.note.like('%Status changed from%')
            ).count()
            
            # Get logs by month for the last 6 months
            from datetime import timedelta
            six_months_ago = datetime.now(timezone.utc) - timedelta(days=180)
            recent_logs = query.filter(
                JobLog.created_at >= six_months_ago
            ).count()
            
            return {
                'total_logs': total_logs,
                'status_change_logs': status_change_logs,
                'regular_logs': total_logs - status_change_logs,
                'recent_logs': recent_logs
            }
        except Exception as e:
            self.logger.error(f"Error getting log statistics: {str(e)}")
            return {
                'total_logs': 0,
                'status_change_logs': 0,
                'regular_logs': 0,
                'recent_logs': 0
            }
    
    def search_logs(self, search_term, job_id=None):
        """
        Search logs by content
        
        Args:
            search_term: Term to search for
            job_id: Optional job ID filter
            
        Returns:
            List of JobLog instances matching the search
        """
        try:
            search_pattern = f'%{search_term}%'
            query = JobLog.query.filter(
                JobLog.note.ilike(search_pattern)
            )
            
            if job_id:
                query = query.filter(JobLog.job_id == job_id)
            
            return query.order_by(JobLog.created_at.desc()).all()
        except Exception as e:
            self.logger.error(f"Error searching logs: {str(e)}")
            return []

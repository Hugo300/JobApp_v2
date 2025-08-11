"""
Test routes
"""
import pytest
from flask import url_for
from models import db, JobApplication, ApplicationStatus, JobLog


class TestMainRoutes:
    """Test main routes"""
    
    def test_dashboard_loads(self, client):
        """Test dashboard loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Job Application Manager' in response.data
    
    def test_dashboard_with_jobs(self, client, sample_job):
        """Test dashboard displays jobs"""
        response = client.get('/')
        assert response.status_code == 200
        assert sample_job.company.encode() in response.data
        assert sample_job.title.encode() in response.data
    
    def test_user_data_get(self, client):
        """Test user data page loads"""
        response = client.get('/user')
        assert response.status_code == 200
        assert b'User Profile' in response.data or b'Profile' in response.data
    
    def test_user_data_post(self, client, app):
        """Test user data creation"""
        with app.app_context():
            response = client.post('/user', data={
                'name': 'Test User',
                'email': 'test@example.com',
                'phone': '123-456-7890',
                'linkedin': 'https://linkedin.com/in/test',
                'github': 'https://github.com/test',
                'skills': 'Python, Flask'
            }, follow_redirects=True)
            assert response.status_code == 200
            assert b'updated successfully' in response.data


class TestJobRoutes:
    """Test job routes"""
    
    def test_new_job_get(self, client):
        """Test new job form loads"""
        response = client.get('/job/new_job')
        assert response.status_code == 200
        assert b'New Job Application' in response.data
    
    def test_new_job_post(self, client, app):
        """Test job creation"""
        with app.app_context():
            response = client.post('/job/new_job', data={
                'company': 'Test Company',
                'title': 'Software Developer',
                'description': 'Test job description',
                'url': 'https://example.com/job'
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Check job was created
            job = JobApplication.query.filter_by(company='Test Company').first()
            assert job is not None
            assert job.title == 'Software Developer'
    
    def test_job_detail(self, client, sample_job):
        """Test job detail page"""
        response = client.get(f'/job/{sample_job.id}')
        assert response.status_code == 200
        assert sample_job.company.encode() in response.data
        assert sample_job.title.encode() in response.data
    
    def test_job_detail_not_found(self, client):
        """Test job detail with invalid ID"""
        response = client.get('/job/999')
        assert response.status_code == 404
    
    def test_add_log_get(self, client, sample_job):
        """Test add log form loads"""
        response = client.get(f'/job/{sample_job.id}/add-log')
        assert response.status_code == 200
        assert b'Add Log Entry' in response.data
    
    def test_add_log_post(self, client, app, sample_job):
        """Test log creation"""
        with app.app_context():
            response = client.post(f'/job/{sample_job.id}/add-log', data={
                'note': 'Test log entry',
                'status_change': ''
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Check log was created
            log = JobLog.query.filter_by(job_id=sample_job.id).first()
            assert log is not None
            assert 'Test log entry' in log.note
    
    def test_add_log_with_status_change(self, client, app, sample_job):
        """Test log creation with status change"""
        with app.app_context():
            original_status = sample_job.status
            response = client.post(f'/job/{sample_job.id}/add-log', data={
                'note': 'Applied to job',
                'status_change': ApplicationStatus.APPLIED.value
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Check status was updated
            db.session.refresh(sample_job)
            assert sample_job.status == ApplicationStatus.APPLIED.value
            
            # Check log was created with status change
            log = JobLog.query.filter_by(job_id=sample_job.id).first()
            assert log is not None
            assert log.status_change_from == original_status
            assert log.status_change_to == ApplicationStatus.APPLIED.value
    
    def test_update_status(self, client, app, sample_job):
        """Test status update"""
        with app.app_context():
            response = client.post(f'/job/{sample_job.id}/update-status', data={
                'status': ApplicationStatus.APPLIED.value
            }, follow_redirects=True)
            assert response.status_code == 200
            
            # Check status was updated
            db.session.refresh(sample_job)
            assert sample_job.status == ApplicationStatus.APPLIED.value

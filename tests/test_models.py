"""
Test models
"""
import pytest
from datetime import datetime
from models import UserData, JobApplication, ApplicationStatus, MasterTemplate, JobLog, Document


class TestUserData:
    """Test UserData model"""
    
    def test_user_creation(self, app):
        """Test user creation"""
        with app.app_context():
            user = UserData(
                name="Test User",
                email="test@example.com",
                skills="Python, Flask"
            )
            assert user.name == "Test User"
            assert user.email == "test@example.com"
            assert user.skills == "Python, Flask"
    
    def test_get_skills_list(self, app):
        """Test skills list conversion"""
        with app.app_context():
            user = UserData(
                name="Test User",
                email="test@example.com",
                skills="Python, Flask, JavaScript, SQL"
            )
            skills_list = user.get_skills_list()
            assert skills_list == ["Python", "Flask", "JavaScript", "SQL"]
    
    def test_get_skills_list_empty(self, app):
        """Test empty skills list"""
        with app.app_context():
            user = UserData(
                name="Test User",
                email="test@example.com",
                skills=""
            )
            skills_list = user.get_skills_list()
            assert skills_list == []


class TestJobApplication:
    """Test JobApplication model"""
    
    def test_job_creation(self, app):
        """Test job application creation"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Software Developer",
                description="Test job description"
            )
            assert job.company == "Test Company"
            assert job.title == "Software Developer"
            assert job.status == ApplicationStatus.COLLECTED.value
    
    def test_status_enum_property(self, app):
        """Test status enum property"""
        with app.app_context():
            job = JobApplication(
                company="Test Company",
                title="Software Developer"
            )
            job.status_enum = ApplicationStatus.APPLIED
            assert job.status == ApplicationStatus.APPLIED.value
            assert job.status_enum == ApplicationStatus.APPLIED


class TestJobLog:
    """Test JobLog model"""
    
    def test_log_creation(self, app, sample_job):
        """Test log entry creation"""
        with app.app_context():
            log = JobLog(
                job_id=sample_job.id,
                note="Test log entry"
            )
            assert log.job_id == sample_job.id
            assert log.note == "Test log entry"
            assert log.created_at is not None
    
    def test_log_with_status_change(self, app, sample_job):
        """Test log entry with status change"""
        with app.app_context():
            log = JobLog(
                job_id=sample_job.id,
                note="Applied to job",
                status_change_from=ApplicationStatus.COLLECTED.value,
                status_change_to=ApplicationStatus.APPLIED.value
            )
            assert log.status_change_from == ApplicationStatus.COLLECTED.value
            assert log.status_change_to == ApplicationStatus.APPLIED.value


class TestMasterTemplate:
    """Test MasterTemplate model"""
    
    def test_template_creation(self, app):
        """Test template creation"""
        with app.app_context():
            template = MasterTemplate(
                name="Test Template",
                content="Test LaTeX content"
            )
            assert template.name == "Test Template"
            assert template.content == "Test LaTeX content"
            assert template.created_at is not None
    
    def test_get_content(self, app):
        """Test get_content method"""
        with app.app_context():
            template = MasterTemplate(
                name="Test Template",
                content="Test LaTeX content"
            )
            assert template.get_content() == "Test LaTeX content"

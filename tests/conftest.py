"""
Test configuration and fixtures
"""
import pytest
import tempfile
import os
from app import create_app
from models import db, UserData, JobApplication, ApplicationStatus, MasterTemplate, JobLog


@pytest.fixture
def app():
    """Create application for testing"""
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp()
    
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
    
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create test CLI runner"""
    return app.test_cli_runner()


@pytest.fixture
def sample_user(app):
    """Create a sample user for testing"""
    with app.app_context():
        user = UserData(
            name="Test User",
            email="test@example.com",
            phone="123-456-7890",
            linkedin="https://linkedin.com/in/testuser",
            github="https://github.com/testuser",
            skills="Python, Flask, JavaScript, SQL"
        )
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def sample_job(app):
    """Create a sample job application for testing"""
    with app.app_context():
        job = JobApplication(
            company="Test Company",
            title="Software Developer",
            description="A test job for software development",
            status=ApplicationStatus.COLLECTED.value,
            url="https://example.com/job"
        )
        db.session.add(job)
        db.session.commit()
        return job


@pytest.fixture
def sample_template(app):
    """Create a sample template for testing"""
    with app.app_context():
        template = MasterTemplate(
            name="Test Template",
            content="\\documentclass{article}\n\\begin{document}\nTest content\n\\end{document}"
        )
        db.session.add(template)
        db.session.commit()
        return template


@pytest.fixture
def sample_log(app, sample_job):
    """Create a sample log entry for testing"""
    with app.app_context():
        log = JobLog(
            job_id=sample_job.id,
            note="Test log entry",
            status_change_from=ApplicationStatus.COLLECTED.value,
            status_change_to=ApplicationStatus.APPLIED.value
        )
        db.session.add(log)
        db.session.commit()
        return log

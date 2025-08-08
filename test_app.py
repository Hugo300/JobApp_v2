#!/usr/bin/env python3
"""
Simple test script to verify the Flask application setup
"""

import sys
import os

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_application():
    print("Testing Flask application setup...")
    
    try:
        # Test imports
        print("✓ All imports successful")
        
        # Test app creation
        from app import create_app
        app = create_app()
        print("✓ Application created successfully")
        
        # Test database
        with app.app_context():
            from models import db, UserData, MasterTemplate, JobApplication, ApplicationStatus, TemplateType
            db.create_all()
            print("✓ Database tables created successfully")
            
            # Test UserData model
            user = UserData(name="Test User", email="test@example.com")
            print("✓ UserData model test successful")
            
            # Test MasterTemplate model
            template = MasterTemplate(name="Test Template", content="Test content")
            print("✓ MasterTemplate model test successful")
            
            # Test JobApplication model with enum
            job = JobApplication(company="Test Company", title="Test Job")
            print("✓ JobApplication model test successful")
            
            # Test ApplicationStatus enum
            print("Testing ApplicationStatus enum...")
            statuses = [status.value for status in ApplicationStatus]
            expected_statuses = ["Collected", "Applied", "Process", "Waiting Decision", "Completed", "Rejected"]
            assert statuses == expected_statuses, f"Expected {expected_statuses}, got {statuses}"
            print("✓ ApplicationStatus enum test successful")
            
            # Test enum property
            job.status_enum = ApplicationStatus.APPLIED
            assert job.status == "Applied", f"Expected 'Applied', got {job.status}"
            print("✓ JobApplication status_enum property test successful")
            
            # Test TemplateType enum
            print("Testing TemplateType enum...")
            template_types = [ttype.value for ttype in TemplateType]
            expected_types = ["database", "file"]
            assert template_types == expected_types, f"Expected {expected_types}, got {template_types}"
            print("✓ TemplateType enum test successful")
            
            # Test file-based template functionality
            print("Testing file-based template functionality...")
            
            # Create a test file for the template
            test_file_path = "documents/templates_latex/test_template.tex"
            os.makedirs(os.path.dirname(test_file_path), exist_ok=True)
            with open(test_file_path, 'w', encoding='utf-8') as f:
                f.write("Test content")
            
            file_template = MasterTemplate(
                name="Test File Template",
                content="Test content",
                template_type=TemplateType.FILE.value,
                file_path=test_file_path
            )
            
            # Test get_content method
            content = file_template.get_content()
            assert content == "Test content", f"Expected 'Test content', got {content}"
            print("✓ File-based template get_content test successful")
            
            # Test save_content method
            success = file_template.save_content("New content")
            assert success == True, "save_content should return True"
            
            # Verify the content was saved
            with open(test_file_path, 'r', encoding='utf-8') as f:
                saved_content = f.read()
            assert saved_content == "New content", f"Expected 'New content', got {saved_content}"
            print("✓ File-based template save_content test successful")
            
            # Clean up test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
        
        print("\n🎉 All tests passed! The application is ready to run.")
        print("To start the application, run:")
        print("python app.py")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_application()

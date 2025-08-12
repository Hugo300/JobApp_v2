"""
Tests for refactored skill services
"""
import pytest
from models import db, SkillBlacklist, Category, CategoryItem, CategoryType
from services.skill_blacklist_service import SkillBlacklistService
from services.category_service import CategoryService


class TestSkillBlacklistService:
    """Test refactored SkillBlacklistService"""
    
    def test_add_to_blacklist(self, app):
        """Test adding skill to blacklist"""
        with app.app_context():
            service = SkillBlacklistService()
            
            success, entry, message = service.add_to_blacklist("Test Skill", "Test reason", "test_user")
            
            assert success is True
            assert entry is not None
            assert entry.skill_text == "Test Skill"
            assert entry.reason == "Test reason"
            assert entry.created_by == "test_user"
            assert "successfully" in message
    
    def test_add_duplicate_to_blacklist(self, app):
        """Test adding duplicate skill to blacklist"""
        with app.app_context():
            service = SkillBlacklistService()
            
            # Add first time
            service.add_to_blacklist("Test Skill", "Test reason")
            
            # Try to add again
            success, entry, message = service.add_to_blacklist("Test Skill", "New reason")
            
            assert success is False
            assert "already blacklisted" in message
    
    def test_is_blacklisted(self, app):
        """Test checking if skill is blacklisted"""
        with app.app_context():
            service = SkillBlacklistService()
            
            service.add_to_blacklist("Blacklisted Skill")
            
            assert service.is_blacklisted("Blacklisted Skill") is True
            assert service.is_blacklisted("Not Blacklisted") is False
    
    def test_filter_blacklisted_skills(self, app):
        """Test filtering blacklisted skills"""
        with app.app_context():
            service = SkillBlacklistService()
            
            service.add_to_blacklist("Bad Skill")
            
            skills = ["Good Skill", "Bad Skill", "Another Good Skill"]
            filtered, blacklisted = service.filter_blacklisted_skills(skills)
            
            assert len(filtered) == 2
            assert len(blacklisted) == 1
            assert "Good Skill" in filtered
            assert "Another Good Skill" in filtered
            assert "Bad Skill" in blacklisted
    
    def test_bulk_add_to_blacklist(self, app):
        """Test bulk adding skills to blacklist"""
        with app.app_context():
            service = SkillBlacklistService()
            
            skills = ["Skill 1", "Skill 2", "Skill 3"]
            results = service.bulk_add_to_blacklist(skills, "Bulk test")
            
            assert results['total_processed'] == 3
            assert len(results['added']) == 3
            assert len(results['skipped']) == 0
            assert len(results['errors']) == 0
    
    def test_get_skill_suggestions(self, app):
        """Test getting skill suggestions for blacklist"""
        with app.app_context():
            from models import JobApplication
            
            service = SkillBlacklistService()
            
            # Create a job with suspicious skills
            job = JobApplication(
                company="Test Company",
                title="Test Job",
                description="Test description"
            )
            job.set_extracted_skills(["Python", "5 years experience", "Good communication skills"])
            db.session.add(job)
            db.session.commit()
            
            suggestions = service.get_skill_suggestions_for_blacklist()
            
            # Should suggest the suspicious skills
            suspicious_skills = [s['skill'] for s in suggestions]
            assert "5 years experience" in suspicious_skills
            assert "Good communication skills" in suspicious_skills
            assert "Python" not in suspicious_skills  # This is a valid skill
    
    def test_suspicious_skill_detection(self, app):
        """Test suspicious skill detection"""
        with app.app_context():
            service = SkillBlacklistService()
            
            # Valid skills should not be suspicious
            assert service._is_suspicious_skill("Python") is False
            assert service._is_suspicious_skill("JavaScript") is False
            assert service._is_suspicious_skill("SQL") is False
            
            # Suspicious skills should be detected
            assert service._is_suspicious_skill("5 years experience") is True
            assert service._is_suspicious_skill("Good communication skills") is True
            assert service._is_suspicious_skill("Bachelor's degree required") is True
            assert service._is_suspicious_skill("Strong background in") is True


class TestCategoryService:
    """Test refactored CategoryService"""
    
    def test_create_category(self, app):
        """Test creating category with improved model"""
        with app.app_context():
            service = CategoryService()
            
            success, category, error = service.create_category(
                "Test Category", "skill", "Test description"
            )
            
            assert success is True
            assert category is not None
            assert category.name == "Test Category"
            assert category.category_type == "skill"
            assert category.description == "Test description"
            assert error is None
    
    def test_create_duplicate_category(self, app):
        """Test creating duplicate category"""
        with app.app_context():
            service = CategoryService()
            
            # Create first category
            service.create_category("Test Category", "skill")
            
            # Try to create duplicate
            success, category, error = service.create_category("Test Category", "skill")
            
            assert success is False
            assert category is None
            assert "already exists" in error
    
    def test_create_category_item(self, app):
        """Test creating category item with improved model"""
        with app.app_context():
            service = CategoryService()
            
            # Create category first
            success, category, _ = service.create_category("Test Category", "skill")
            
            # Create item
            success, item, error = service.create_category_item(
                category.id, "Test Item", "Test description", ["keyword1", "keyword2"]
            )
            
            assert success is True
            assert item is not None
            assert item.name == "Test Item"
            assert item.description == "Test description"
            assert item.get_keywords_list() == ["keyword1", "keyword2"]
            assert error is None
    
    def test_update_category(self, app):
        """Test updating category"""
        with app.app_context():
            service = CategoryService()
            
            # Create category
            success, category, _ = service.create_category("Original Name", "skill")
            
            # Update category
            success, error = service.update_category(
                category.id, name="Updated Name", description="Updated description"
            )
            
            assert success is True
            assert error is None
            
            # Verify update
            updated_category = db.session.get(Category, category.id)
            assert updated_category.name == "Updated Name"
            assert updated_category.description == "Updated description"
    
    def test_update_category_item(self, app):
        """Test updating category item"""
        with app.app_context():
            service = CategoryService()
            
            # Create category and item
            success, category, _ = service.create_category("Test Category", "skill")
            success, item, _ = service.create_category_item(category.id, "Original Item")
            
            # Update item
            success, error = service.update_category_item(
                item.id, name="Updated Item", keywords=["new", "keywords"]
            )
            
            assert success is True
            assert error is None
            
            # Verify update
            updated_item = db.session.get(CategoryItem, item.id)
            assert updated_item.name == "Updated Item"
            assert updated_item.get_keywords_list() == ["new", "keywords"]
    
    def test_delete_category(self, app):
        """Test deleting (deactivating) category"""
        with app.app_context():
            service = CategoryService()
            
            # Create category
            success, category, _ = service.create_category("Test Category", "skill")
            
            # Delete category
            success, error = service.delete_category(category.id)
            
            assert success is True
            assert error is None
            
            # Verify deactivation
            deleted_category = db.session.get(Category, category.id)
            assert deleted_category.is_active is False
    
    def test_delete_system_category_fails(self, app):
        """Test that system categories cannot be deleted"""
        with app.app_context():
            service = CategoryService()
            
            # Create system category
            success, category, _ = service.create_category("System Category", "skill", is_system=True)
            
            # Try to delete system category
            success, error = service.delete_category(category.id)
            
            assert success is False
            assert "Cannot deactivate system categories" in error
    
    def test_get_category_statistics(self, app):
        """Test getting category statistics"""
        with app.app_context():
            service = CategoryService()
            
            # Create some test data
            service.create_category("Skill Category", "skill")
            service.create_category("Industry Category", "industry")
            service.create_category("System Category", "skill", is_system=True)
            
            stats = service.get_category_statistics()
            
            assert stats['total_categories'] == 3
            assert stats['active_categories'] == 3
            assert stats['system_categories'] == 1
            assert stats['custom_categories'] == 2
            assert 'by_type' in stats
            assert 'skill' in stats['by_type']
            assert 'industry' in stats['by_type']

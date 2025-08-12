"""
Tests for skill-related models
"""
import pytest
from datetime import datetime
from models import db, SkillBlacklist, Category, CategoryItem, CategoryType


class TestSkillBlacklist:
    """Test SkillBlacklist model"""
    
    def test_create_skill_blacklist(self, app):
        """Test creating a skill blacklist entry"""
        with app.app_context():
            skill = SkillBlacklist.create("Test Skill", "Not a real skill", "test_user")
            db.session.add(skill)
            db.session.commit()
            
            assert skill.skill_text == "Test Skill"
            assert skill.reason == "Not a real skill"
            assert skill.created_by == "test_user"
            assert skill.is_active is True
            assert skill.created_at is not None
    
    def test_create_duplicate_skill_blacklist(self, app):
        """Test creating duplicate skill blacklist entry"""
        with app.app_context():
            skill1 = SkillBlacklist.create("Test Skill", "Reason 1")
            db.session.add(skill1)
            db.session.commit()
            
            # Should raise error for duplicate
            with pytest.raises(ValueError, match="already blacklisted"):
                SkillBlacklist.create("Test Skill", "Reason 2")
    
    def test_create_empty_skill_text(self, app):
        """Test creating blacklist with empty skill text"""
        with app.app_context():
            with pytest.raises(ValueError, match="cannot be empty"):
                SkillBlacklist.create("")
            
            with pytest.raises(ValueError, match="cannot be empty"):
                SkillBlacklist.create("   ")
    
    def test_create_long_skill_text(self, app):
        """Test creating blacklist with too long skill text"""
        with app.app_context():
            long_text = "x" * 201
            with pytest.raises(ValueError, match="cannot exceed 200 characters"):
                SkillBlacklist.create(long_text)
    
    def test_reactivate_deactivated_skill(self, app):
        """Test reactivating a deactivated skill"""
        with app.app_context():
            skill = SkillBlacklist.create("Test Skill", "Original reason")
            db.session.add(skill)
            db.session.commit()
            
            # Deactivate
            skill.deactivate()
            db.session.commit()
            assert skill.is_active is False
            
            # Try to create again - should reactivate
            reactivated = SkillBlacklist.create("Test Skill", "New reason")
            assert reactivated.id == skill.id
            assert reactivated.is_active is True
            assert reactivated.reason == "New reason"
    
    def test_is_blacklisted(self, app):
        """Test checking if skill is blacklisted"""
        with app.app_context():
            skill = SkillBlacklist.create("Blacklisted Skill")
            db.session.add(skill)
            db.session.commit()
            
            assert SkillBlacklist.is_blacklisted("Blacklisted Skill") is True
            assert SkillBlacklist.is_blacklisted("Not Blacklisted") is False
            assert SkillBlacklist.is_blacklisted("") is False
            assert SkillBlacklist.is_blacklisted(None) is False
    
    def test_get_active_blacklist(self, app):
        """Test getting active blacklist"""
        with app.app_context():
            skill1 = SkillBlacklist.create("Active Skill")
            skill2 = SkillBlacklist.create("Inactive Skill")
            db.session.add_all([skill1, skill2])
            db.session.commit()
            
            skill2.deactivate()
            db.session.commit()
            
            active_skills = SkillBlacklist.get_active_blacklist()
            assert len(active_skills) == 1
            assert active_skills[0].skill_text == "Active Skill"
    
    def test_to_dict(self, app):
        """Test converting to dictionary"""
        with app.app_context():
            skill = SkillBlacklist.create("Test Skill", "Test reason", "test_user")
            db.session.add(skill)
            db.session.commit()
            
            data = skill.to_dict()
            assert data['skill_text'] == "Test Skill"
            assert data['reason'] == "Test reason"
            assert data['created_by'] == "test_user"
            assert data['is_active'] is True
            assert 'created_at' in data
            assert 'updated_at' in data


class TestCategory:
    """Test Category model"""
    
    def test_create_category(self, app):
        """Test creating a category"""
        with app.app_context():
            category = Category.create("Test Category", "skill", "Test description")
            db.session.add(category)
            db.session.commit()
            
            assert category.name == "Test Category"
            assert category.category_type == "skill"
            assert category.description == "Test description"
            assert category.is_active is True
            assert category.created_at is not None
    
    def test_create_duplicate_category(self, app):
        """Test creating duplicate category"""
        with app.app_context():
            cat1 = Category.create("Test Category", "skill")
            db.session.add(cat1)
            db.session.commit()
            
            with pytest.raises(ValueError, match="already exists"):
                Category.create("Test Category", "skill")
    
    def test_create_empty_name(self, app):
        """Test creating category with empty name"""
        with app.app_context():
            with pytest.raises(ValueError, match="cannot be empty"):
                Category.create("", "skill")
    
    def test_create_long_name(self, app):
        """Test creating category with too long name"""
        with app.app_context():
            long_name = "x" * 101
            with pytest.raises(ValueError, match="cannot exceed 100 characters"):
                Category.create(long_name, "skill")
    
    def test_invalid_category_type(self, app):
        """Test creating category with invalid type"""
        with app.app_context():
            category = Category.create("Test Category", "invalid_type")
            assert category.category_type == "custom"  # Should default to custom
    
    def test_color_validation(self, app):
        """Test color validation"""
        with app.app_context():
            # Test color without #
            category1 = Category.create("Test 1", "skill", color="ff0000")
            assert category1.color == "#ff0000"
            
            # Test invalid color length
            category2 = Category.create("Test 2", "skill", color="#ff")
            assert category2.color == "#6c757d"  # Should default
    
    def test_update_category(self, app):
        """Test updating category"""
        with app.app_context():
            category = Category.create("Original Name", "skill")
            db.session.add(category)
            db.session.commit()
            
            category.update(name="Updated Name", description="New description")
            assert category.name == "Updated Name"
            assert category.description == "New description"
    
    def test_update_system_category_name(self, app):
        """Test updating system category name should fail"""
        with app.app_context():
            category = Category.create("System Category", "skill", is_system=True)
            db.session.add(category)
            db.session.commit()
            
            with pytest.raises(ValueError, match="Cannot rename system categories"):
                category.update(name="New Name")
    
    def test_deactivate_system_category(self, app):
        """Test deactivating system category should fail"""
        with app.app_context():
            category = Category.create("System Category", "skill", is_system=True)
            db.session.add(category)
            db.session.commit()
            
            with pytest.raises(ValueError, match="Cannot deactivate system categories"):
                category.deactivate()
    
    def test_category_type_enum_property(self, app):
        """Test category type enum property"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            assert category.category_type_enum == CategoryType.SKILL
            
            category.category_type_enum = CategoryType.INDUSTRY
            assert category.category_type == "industry"
    
    def test_to_dict(self, app):
        """Test converting to dictionary"""
        with app.app_context():
            category = Category.create("Test Category", "skill", "Description")
            db.session.add(category)
            db.session.commit()
            
            data = category.to_dict()
            assert data['name'] == "Test Category"
            assert data['category_type'] == "skill"
            assert data['description'] == "Description"
            assert data['is_active'] is True
            assert 'item_count' in data
            assert 'total_usage_count' in data


class TestCategoryItem:
    """Test CategoryItem model"""
    
    def test_create_category_item(self, app):
        """Test creating a category item"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            db.session.add(category)
            db.session.commit()
            
            item = CategoryItem.create(category.id, "Test Item", "Description", ["keyword1", "keyword2"])
            db.session.add(item)
            db.session.commit()
            
            assert item.name == "Test Item"
            assert item.normalized_name == "test item"
            assert item.description == "Description"
            assert item.get_keywords_list() == ["keyword1", "keyword2"]
    
    def test_normalize_name(self, app):
        """Test name normalization"""
        assert CategoryItem.normalize_name("  Test Name  ") == "test name"
        assert CategoryItem.normalize_name("UPPERCASE") == "uppercase"
        assert CategoryItem.normalize_name("") == ""
    
    def test_create_duplicate_item(self, app):
        """Test creating duplicate item in same category"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            db.session.add(category)
            db.session.commit()
            
            item1 = CategoryItem.create(category.id, "Test Item")
            db.session.add(item1)
            db.session.commit()
            
            with pytest.raises(ValueError, match="already exists"):
                CategoryItem.create(category.id, "Test Item")
    
    def test_matches_text(self, app):
        """Test text matching functionality"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            db.session.add(category)
            db.session.commit()
            
            item = CategoryItem.create(category.id, "Python Programming", keywords=["python", "programming"])
            db.session.add(item)
            db.session.commit()
            
            assert item.matches_text("Python developer") is True
            assert item.matches_text("programming skills") is True
            assert item.matches_text("Java developer") is False
    
    def test_increment_usage(self, app):
        """Test incrementing usage count"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            db.session.add(category)
            db.session.commit()
            
            item = CategoryItem.create(category.id, "Test Item")
            db.session.add(item)
            db.session.commit()
            
            assert item.usage_count == 0
            item.increment_usage()
            assert item.usage_count == 1
    
    def test_to_dict(self, app):
        """Test converting to dictionary"""
        with app.app_context():
            category = Category.create("Test Category", "skill")
            db.session.add(category)
            db.session.commit()
            
            item = CategoryItem.create(category.id, "Test Item", "Description", ["keyword"])
            db.session.add(item)
            db.session.commit()
            
            data = item.to_dict()
            assert data['name'] == "Test Item"
            assert data['normalized_name'] == "test item"
            assert data['description'] == "Description"
            assert data['keywords'] == ["keyword"]
            assert data['category_name'] == "Test Category"

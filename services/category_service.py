"""
Category management service for flexible categorization system
"""
import json
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime, timezone
from models import db, Category, CategoryItem, CategoryType
from .database_service import db_service, DatabaseError
from utils.validation import ValidationResult


class CategoryService:
    """Service for managing categories and category items"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_category(self, name: str, category_type: str, description: Optional[str] = None,
                       color: Optional[str] = None, icon: Optional[str] = None,
                       is_system: bool = False) -> Tuple[bool, Optional[Category], Optional[str]]:
        """
        Create a new category using improved model method

        Args:
            name: Category name
            category_type: Type of category (skill, industry, etc.)
            description: Optional description
            color: Hex color code for UI
            icon: FontAwesome icon class
            is_system: Whether this is a system category

        Returns:
            Tuple[bool, Optional[Category], Optional[str]]: (success, category, error_message)
        """
        try:
            # Set defaults if not provided
            if not color:
                color = self._get_default_color_for_type(category_type)
            if not icon:
                icon = self._get_default_icon_for_type(category_type)

            # Use improved model method for creation and validation
            category = Category.create(
                name=name,
                category_type=category_type,
                description=description,
                color=color,
                icon=icon,
                is_system=is_system
            )

            db.session.add(category)
            db.session.commit()

            self.logger.info(f"Created category: {name} ({category_type})")
            return True, category, None

        except ValueError as e:
            # Model validation error
            self.logger.warning(f"Validation error creating category: {str(e)}")
            return False, None, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating category: {str(e)}")
            return False, None, f"Error creating category: {str(e)}"

    def get_category_by_id(self, category_id: int) -> Optional[Category]:
        """Get a category by ID"""
        try:
            return db.session.get(Category, category_id)
        except Exception as e:
            self.logger.error(f"Error getting category by ID {category_id}: {str(e)}")
            return None
    
    def get_categories_by_type(self, category_type: str, active_only: bool = True) -> List[Category]:
        """Get all categories of a specific type"""
        try:
            query = Category.query.filter_by(category_type=category_type)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.order_by(Category.name).all()
        except Exception as e:
            self.logger.error(f"Error getting categories by type {category_type}: {str(e)}")
            return []
    
    def get_all_categories(self, active_only: bool = True) -> List[Category]:
        """Get all categories"""
        try:
            query = Category.query
            if active_only:
                query = query.filter_by(is_active=True)
            return query.order_by(Category.category_type, Category.name).all()
        except Exception as e:
            self.logger.error(f"Error getting all categories: {str(e)}")
            return []
    
    def create_category_item(self, category_id: int, name: str, description: Optional[str] = None,
                           keywords: Optional[List[str]] = None) -> Tuple[bool, Optional[CategoryItem], Optional[str]]:
        """
        Create a new category item
        
        Args:
            category_id: ID of the parent category
            name: Item name
            description: Optional description
            keywords: List of keywords for matching
            
        Returns:
            Tuple[bool, Optional[CategoryItem], Optional[str]]: (success, item, error_message)
        """
        try:
            # Check if category exists
            category = db.session.get(Category, category_id)
            if not category:
                return False, None, "Category not found"

            # Use improved model method for creation and validation
            item = CategoryItem.create(
                category_id=category_id,
                name=name,
                description=description,
                keywords=keywords
            )

            db.session.add(item)
            db.session.commit()

            self.logger.info(f"Created category item: {name} in {category.name}")
            return True, item, None

        except ValueError as e:
            # Model validation error
            self.logger.warning(f"Validation error creating category item: {str(e)}")
            return False, None, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating category item: {str(e)}")
            return False, None, f"Error creating category item: {str(e)}"
    
    def get_category_items(self, category_id: int, active_only: bool = True) -> List[CategoryItem]:
        """Get all items in a category"""
        try:
            query = CategoryItem.query.filter_by(category_id=category_id)
            if active_only:
                query = query.filter_by(is_active=True)
            return query.order_by(CategoryItem.name).all()
        except Exception as e:
            self.logger.error(f"Error getting category items for category {category_id}: {str(e)}")
            return []
    
    def find_category_item_by_name(self, category_type: str, item_name: str) -> Optional[CategoryItem]:
        """Find a category item by name within a category type"""
        try:
            normalized_name = item_name.strip().lower()
            return CategoryItem.query.join(Category).filter(
                Category.category_type == category_type,
                CategoryItem.normalized_name == normalized_name,
                CategoryItem.is_active == True,
                Category.is_active == True
            ).first()
        except Exception as e:
            self.logger.error(f"Error finding category item: {str(e)}")
            return None
    
    def match_items_by_keywords(self, category_type: str, text: str) -> List[CategoryItem]:
        """Match category items by keywords in text"""
        try:
            items = []
            categories = self.get_categories_by_type(category_type)
            
            for category in categories:
                category_items = self.get_category_items(category.id)
                for item in category_items:
                    if self._item_matches_text(item, text):
                        items.append(item)
            
            return items
        except Exception as e:
            self.logger.error(f"Error matching items by keywords: {str(e)}")
            return []
    
    def _item_matches_text(self, item: CategoryItem, text: str) -> bool:
        """Check if an item matches the given text using improved model method"""
        return item.matches_text(text)

    def update_category(self, category_id: int, name: str = None, description: str = None,
                       color: str = None, icon: str = None) -> Tuple[bool, Optional[str]]:
        """Update a category using improved model method"""
        try:
            category = db.session.get(Category, category_id)
            if not category:
                return False, "Category not found"

            category.update(name=name, description=description, color=color, icon=icon)
            db.session.commit()

            self.logger.info(f"Updated category: {category.name}")
            return True, None

        except ValueError as e:
            self.logger.warning(f"Validation error updating category: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating category: {str(e)}")
            return False, f"Error updating category: {str(e)}"

    def update_category_item(self, item_id: int, name: str = None, description: str = None,
                            keywords: List[str] = None) -> Tuple[bool, Optional[str]]:
        """Update a category item using improved model method"""
        try:
            item = db.session.get(CategoryItem, item_id)
            if not item:
                return False, "Category item not found"

            item.update(name=name, description=description, keywords=keywords)
            db.session.commit()

            self.logger.info(f"Updated category item: {item.name}")
            return True, None

        except ValueError as e:
            self.logger.warning(f"Validation error updating category item: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error updating category item: {str(e)}")
            return False, f"Error updating category item: {str(e)}"

    def delete_category(self, category_id: int) -> Tuple[bool, Optional[str]]:
        """Delete (deactivate) a category"""
        try:
            category = db.session.get(Category, category_id)
            if not category:
                return False, "Category not found"

            category.deactivate()
            db.session.commit()

            self.logger.info(f"Deactivated category: {category.name}")
            return True, None

        except ValueError as e:
            self.logger.warning(f"Cannot deactivate category: {str(e)}")
            return False, str(e)
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deactivating category: {str(e)}")
            return False, f"Error deactivating category: {str(e)}"

    def delete_category_item(self, item_id: int) -> Tuple[bool, Optional[str]]:
        """Delete (deactivate) a category item"""
        try:
            item = db.session.get(CategoryItem, item_id)
            if not item:
                return False, "Category item not found"

            item.deactivate()
            db.session.commit()

            self.logger.info(f"Deactivated category item: {item.name}")
            return True, None

        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error deactivating category item: {str(e)}")
            return False, f"Error deactivating category item: {str(e)}"

    def get_category_statistics(self) -> Dict[str, any]:
        """Get comprehensive statistics about categories"""
        try:
            all_categories = Category.query.all()
            active_categories = [cat for cat in all_categories if cat.is_active]

            stats_by_type = {}
            for cat_type in CategoryType:
                type_categories = [cat for cat in active_categories if cat.category_type == cat_type.value]
                total_items = sum(cat.item_count for cat in type_categories)
                total_usage = sum(cat.total_usage_count for cat in type_categories)

                stats_by_type[cat_type.value] = {
                    'category_count': len(type_categories),
                    'total_items': total_items,
                    'total_usage': total_usage,
                    'avg_items_per_category': total_items / len(type_categories) if type_categories else 0
                }

            return {
                'total_categories': len(all_categories),
                'active_categories': len(active_categories),
                'inactive_categories': len(all_categories) - len(active_categories),
                'system_categories': len([cat for cat in active_categories if cat.is_system]),
                'custom_categories': len([cat for cat in active_categories if not cat.is_system]),
                'by_type': stats_by_type
            }

        except Exception as e:
            self.logger.error(f"Error getting category statistics: {str(e)}")
            return {
                'total_categories': 0,
                'active_categories': 0,
                'inactive_categories': 0,
                'system_categories': 0,
                'custom_categories': 0,
                'by_type': {}
            }
    
    def _get_default_color_for_type(self, category_type: str) -> str:
        """Get default color for category type"""
        color_map = {
            CategoryType.SKILL.value: '#007bff',      # Blue
            CategoryType.INDUSTRY.value: '#28a745',   # Green
            CategoryType.TECHNOLOGY.value: '#6f42c1', # Purple
            CategoryType.LOCATION.value: '#fd7e14',   # Orange
            CategoryType.CUSTOM.value: '#6c757d'      # Gray
        }
        return color_map.get(category_type, '#6c757d')
    
    def _get_default_icon_for_type(self, category_type: str) -> str:
        """Get default icon for category type"""
        icon_map = {
            CategoryType.SKILL.value: 'fas fa-cogs',
            CategoryType.INDUSTRY.value: 'fas fa-industry',
            CategoryType.TECHNOLOGY.value: 'fas fa-microchip',
            CategoryType.LOCATION.value: 'fas fa-map-marker-alt',
            CategoryType.CUSTOM.value: 'fas fa-tag'
        }
        return icon_map.get(category_type, 'fas fa-tag')
    
    def initialize_default_categories(self) -> bool:
        """Initialize default system categories"""
        try:
            default_categories = [
                {
                    'name': 'Hard Skills',
                    'category_type': CategoryType.SKILL.value,
                    'description': 'Technical and measurable skills',
                    'is_system': True
                },
                {
                    'name': 'Soft Skills',
                    'category_type': CategoryType.SKILL.value,
                    'description': 'Interpersonal and behavioral skills',
                    'is_system': True
                },
                {
                    'name': 'Industries',
                    'category_type': CategoryType.INDUSTRY.value,
                    'description': 'Industry classifications for jobs',
                    'is_system': True
                }
            ]
            
            created_count = 0
            for cat_data in default_categories:
                success, category, error = self.create_category(**cat_data)
                if success:
                    created_count += 1
                elif "already exists" not in (error or ""):
                    self.logger.warning(f"Failed to create default category {cat_data['name']}: {error}")
            
            self.logger.info(f"Initialized {created_count} default categories")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing default categories: {str(e)}")
            return False

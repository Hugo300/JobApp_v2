from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
import os

# We'll get db from the app context instead of importing directly
db = SQLAlchemy()

class ApplicationStatus(Enum):
    COLLECTED = "Collected"
    APPLIED = "Applied"
    PROCESS = "Process"
    WAITING_DECISION = "Waiting Decision"
    COMPLETED = "Completed"
    REJECTED = "Rejected"

class TemplateType(Enum):
    DATABASE = "database"
    FILE = "file"

class JobMode(Enum):
    REMOTE = "Remote"
    HYBRID = "Hybrid"
    ON_SITE = "On-site"

class UserData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20))
    linkedin = db.Column(db.String(200))
    github = db.Column(db.String(200))
    skills = db.Column(db.Text)  # Comma-separated string
    
    def get_skills_list(self):
        """Convert comma-separated skills string to list"""
        if self.skills:
            return [skill.strip() for skill in self.skills.split(',') if skill.strip()]
        return []

class MasterTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    template_type = db.Column(db.String(20), default=TemplateType.DATABASE.value)
    file_path = db.Column(db.String(500))  # Path to template file if file-based
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    def get_content(self):
        """Get template content, either from database or file"""
        if self.template_type == TemplateType.FILE.value and self.file_path:
            try:
                # Validate file path to prevent directory traversal
                if '..' in self.file_path or self.file_path.startswith('/'):
                    raise ValueError("Invalid file path detected")

                with open(self.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if not content.strip():
                        return f"Template file is empty: {self.file_path}"
                    return content
            except FileNotFoundError:
                return f"Template file not found: {self.file_path}"
            except PermissionError:
                return f"Permission denied reading template file: {self.file_path}"
            except UnicodeDecodeError:
                return f"Template file encoding error: {self.file_path}"
            except ValueError as e:
                return f"Template file error: {str(e)}"
            except Exception as e:
                return f"Unexpected error reading template file: {str(e)}"
        else:
            return self.content or ""
    
    def save_content(self, content):
        """Save template content, either to database or file"""
        if self.template_type == TemplateType.FILE.value and self.file_path:
            try:
                # Validate file path to prevent directory traversal
                if '..' in self.file_path or self.file_path.startswith('/'):
                    raise ValueError("Invalid file path detected")

                # Validate content
                if not isinstance(content, str):
                    raise ValueError("Content must be a string")

                # Create directory if it doesn't exist
                directory = os.path.dirname(self.file_path)
                if directory:
                    os.makedirs(directory, exist_ok=True)

                # Write content to file
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            except (OSError, ValueError, PermissionError) as e:
                # Log the error for debugging
                import logging
                logging.getLogger(__name__).error(f"Error saving template file {self.file_path}: {str(e)}")
                return False
            except Exception as e:
                # Log unexpected errors
                import logging
                logging.getLogger(__name__).error(f"Unexpected error saving template file {self.file_path}: {str(e)}")
                return False
        else:
            try:
                if not isinstance(content, str):
                    raise ValueError("Content must be a string")
                self.content = content
                return True
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Error saving template content: {str(e)}")
                return False

class JobApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(100), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default=ApplicationStatus.COLLECTED.value, nullable=False)
    last_update = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    url = db.Column(db.String(500))

    # New fields for location and job mode
    office_location = db.Column(db.String(200))  # City, office address
    country = db.Column(db.String(100))  # Country
    job_mode = db.Column(db.String(50), default=JobMode.ON_SITE.value)  # Remote, Hybrid, On-site

    # Skills extracted from job description
    extracted_skills = db.Column(db.Text)  # JSON string of extracted skills

    # Industry categorization
    industry_id = db.Column(db.Integer, db.ForeignKey('category_item.id'), nullable=True)

    # Relationships
    documents = db.relationship('Document', backref='job_application', lazy=True, cascade='all, delete-orphan')
    logs = db.relationship('JobLog', backref='job_application', lazy=True, cascade='all, delete-orphan', order_by='JobLog.created_at.desc()')
    industry = db.relationship('CategoryItem', foreign_keys=[industry_id], backref='jobs')
    
    @property
    def status_enum(self):
        """Get the status as an enum"""
        return ApplicationStatus(self.status)
    
    @status_enum.setter
    def status_enum(self, value):
        """Set the status from an enum"""
        if isinstance(value, ApplicationStatus):
            self.status = value.value
        else:
            self.status = value

    @property
    def job_mode_enum(self):
        """Get the job mode as an enum"""
        try:
            return JobMode(self.job_mode)
        except ValueError:
            return JobMode.ON_SITE  # Default fallback

    @job_mode_enum.setter
    def job_mode_enum(self, value):
        """Set the job mode from an enum"""
        if isinstance(value, JobMode):
            self.job_mode = value.value
        else:
            self.job_mode = value

    def get_extracted_skills(self):
        """Get extracted skills as a list"""
        if self.extracted_skills:
            import json
            try:
                return json.loads(self.extracted_skills)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_extracted_skills(self, skills_list):
        """Set extracted skills from a list"""
        if skills_list:
            import json
            self.extracted_skills = json.dumps(skills_list)
        else:
            self.extracted_skills = None

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # CV, Cover Letter
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class JobLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('job_application.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    note = db.Column(db.Text, nullable=False)
    status_change_from = db.Column(db.String(50))  # Previous status if this log represents a status change
    status_change_to = db.Column(db.String(50))    # New status if this log represents a status change

    def __repr__(self):
        return f'<JobLog {self.id}: {self.note[:50]}...>'


class SkillBlacklist(db.Model):
    """Model for managing skills that should be filtered out"""
    __tablename__ = 'skill_blacklist'

    id = db.Column(db.Integer, primary_key=True)
    skill_text = db.Column(db.String(200), nullable=False, unique=True, index=True)
    reason = db.Column(db.String(500))  # Why this was blacklisted
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    created_by = db.Column(db.String(100))  # Who added this to blacklist

    def __repr__(self):
        return f'<SkillBlacklist {self.skill_text}>'

    def __str__(self):
        return self.skill_text

    @classmethod
    def create(cls, skill_text: str, reason: str = None, created_by: str = None):
        """Create a new blacklisted skill with validation"""
        if not skill_text or not skill_text.strip():
            raise ValueError("Skill text cannot be empty")

        skill_text = skill_text.strip()
        if len(skill_text) > 200:
            raise ValueError("Skill text cannot exceed 200 characters")

        # Check if already exists
        existing = cls.query.filter_by(skill_text=skill_text).first()
        if existing:
            if existing.is_active:
                raise ValueError(f"Skill '{skill_text}' is already blacklisted")
            else:
                # Reactivate existing entry
                existing.is_active = True
                existing.reason = reason
                existing.created_by = created_by
                existing.updated_at = datetime.now(timezone.utc)
                return existing

        return cls(
            skill_text=skill_text,
            reason=reason[:500] if reason else None,
            created_by=created_by
        )

    def deactivate(self):
        """Deactivate this blacklist entry"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self, reason: str = None):
        """Reactivate this blacklist entry"""
        self.is_active = True
        if reason:
            self.reason = reason[:500]
        self.updated_at = datetime.now(timezone.utc)

    @classmethod
    def is_blacklisted(cls, skill_text: str) -> bool:
        """Check if a skill is blacklisted"""
        if not skill_text:
            return False
        return cls.query.filter_by(
            skill_text=skill_text.strip(),
            is_active=True
        ).first() is not None

    @classmethod
    def get_active_blacklist(cls):
        """Get all active blacklisted skills"""
        return cls.query.filter_by(is_active=True).order_by(cls.skill_text).all()

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'skill_text': self.skill_text,
            'reason': self.reason,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'created_by': self.created_by
        }


class CategoryType(Enum):
    """Types of categories available in the system"""
    SKILL = "skill"
    INDUSTRY = "industry"
    TECHNOLOGY = "technology"
    LOCATION = "location"
    CUSTOM = "custom"


class Category(db.Model):
    """Model for flexible category management"""
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    category_type = db.Column(db.String(50), nullable=False, index=True)  # skill, industry, technology, etc.
    description = db.Column(db.Text)
    color = db.Column(db.String(7), default='#6c757d')  # Hex color for UI
    icon = db.Column(db.String(50), default='fas fa-tag')  # FontAwesome icon class
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_system = db.Column(db.Boolean, default=False, nullable=False)  # System categories can't be deleted
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    category_items = db.relationship('CategoryItem', backref='category', lazy=True, cascade='all, delete-orphan')

    # Unique constraint on name and type combination
    __table_args__ = (db.UniqueConstraint('name', 'category_type', name='unique_category_name_type'),)

    def __repr__(self):
        return f'<Category {self.name} ({self.category_type})>'

    def __str__(self):
        return f"{self.name} ({self.category_type})"

    @property
    def category_type_enum(self):
        """Get the category type as an enum"""
        try:
            return CategoryType(self.category_type)
        except ValueError:
            return CategoryType.CUSTOM

    @category_type_enum.setter
    def category_type_enum(self, value):
        """Set the category type from an enum"""
        if isinstance(value, CategoryType):
            self.category_type = value.value
        else:
            self.category_type = value

    @classmethod
    def create(cls, name: str, category_type: str, description: str = None,
               color: str = None, icon: str = None, is_system: bool = False):
        """Create a new category with validation"""
        if not name or not name.strip():
            raise ValueError("Category name cannot be empty")

        if not category_type or not category_type.strip():
            raise ValueError("Category type cannot be empty")

        name = name.strip()
        category_type = category_type.strip().lower()

        if len(name) > 100:
            raise ValueError("Category name cannot exceed 100 characters")

        # Validate category type
        valid_types = [ct.value for ct in CategoryType]
        if category_type not in valid_types:
            category_type = CategoryType.CUSTOM.value

        # Validate color format
        if color and not color.startswith('#'):
            color = f"#{color}"
        if color and len(color) != 7:
            color = '#6c757d'

        # Check if already exists
        existing = cls.query.filter_by(name=name, category_type=category_type).first()
        if existing:
            if existing.is_active:
                raise ValueError(f"Category '{name}' of type '{category_type}' already exists")
            else:
                # Reactivate existing category
                existing.is_active = True
                existing.description = description
                existing.color = color or existing.color
                existing.icon = icon or existing.icon
                existing.updated_at = datetime.now(timezone.utc)
                return existing

        return cls(
            name=name,
            category_type=category_type,
            description=description,
            color=color or '#6c757d',
            icon=icon or 'fas fa-tag',
            is_system=is_system
        )

    def update(self, name: str = None, description: str = None,
               color: str = None, icon: str = None):
        """Update category with validation"""
        if self.is_system and name and name != self.name:
            raise ValueError("Cannot rename system categories")

        if name:
            name = name.strip()
            if len(name) > 100:
                raise ValueError("Category name cannot exceed 100 characters")

            # Check for duplicates
            existing = Category.query.filter(
                Category.name == name,
                Category.category_type == self.category_type,
                Category.id != self.id
            ).first()
            if existing:
                raise ValueError(f"Category '{name}' of type '{self.category_type}' already exists")

            self.name = name

        if description is not None:
            self.description = description

        if color:
            if not color.startswith('#'):
                color = f"#{color}"
            if len(color) == 7:
                self.color = color

        if icon:
            self.icon = icon

        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate this category"""
        if self.is_system:
            raise ValueError("Cannot deactivate system categories")
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self):
        """Reactivate this category"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    @property
    def item_count(self):
        """Get count of active items in this category"""
        return len([item for item in self.category_items if item.is_active])

    @property
    def total_usage_count(self):
        """Get total usage count of all items in this category"""
        return sum(item.usage_count for item in self.category_items if item.is_active)

    def get_active_items(self):
        """Get all active items in this category"""
        return [item for item in self.category_items if item.is_active]

    def to_dict(self, include_items: bool = False):
        """Convert to dictionary for API responses"""
        result = {
            'id': self.id,
            'name': self.name,
            'category_type': self.category_type,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_active': self.is_active,
            'is_system': self.is_system,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'item_count': self.item_count,
            'total_usage_count': self.total_usage_count
        }

        if include_items:
            result['items'] = [item.to_dict() for item in self.get_active_items()]

        return result


class CategoryItem(db.Model):
    """Model for items within categories (skills, industries, etc.)"""
    __tablename__ = 'category_item'

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False, index=True)
    name = db.Column(db.String(200), nullable=False)
    normalized_name = db.Column(db.String(200), nullable=False, index=True)  # Lowercase, trimmed for matching
    description = db.Column(db.Text)
    keywords = db.Column(db.Text)  # JSON array of keywords for matching
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    usage_count = db.Column(db.Integer, default=0, nullable=False)  # Track how often this item is used
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Unique constraint on category and normalized name
    __table_args__ = (db.UniqueConstraint('category_id', 'normalized_name', name='unique_category_item'),)

    def __repr__(self):
        return f'<CategoryItem {self.name} in {self.category.name if self.category else "Unknown"}>'

    def __str__(self):
        return self.name

    @staticmethod
    def normalize_name(name: str) -> str:
        """Normalize a name for consistent matching"""
        if not name:
            return ""
        return name.strip().lower()

    @classmethod
    def create(cls, category_id: int, name: str, description: str = None, keywords: list = None):
        """Create a new category item with validation"""
        if not name or not name.strip():
            raise ValueError("Item name cannot be empty")

        name = name.strip()
        if len(name) > 200:
            raise ValueError("Item name cannot exceed 200 characters")

        normalized_name = cls.normalize_name(name)

        # Check if already exists in this category
        existing = cls.query.filter_by(
            category_id=category_id,
            normalized_name=normalized_name
        ).first()

        if existing:
            if existing.is_active:
                raise ValueError(f"Item '{name}' already exists in this category")
            else:
                # Reactivate existing item
                existing.is_active = True
                existing.name = name  # Update display name
                existing.description = description
                if keywords:
                    existing.set_keywords_list(keywords)
                existing.updated_at = datetime.now(timezone.utc)
                return existing

        item = cls(
            category_id=category_id,
            name=name,
            normalized_name=normalized_name,
            description=description
        )

        if keywords:
            item.set_keywords_list(keywords)

        return item

    def update(self, name: str = None, description: str = None, keywords: list = None):
        """Update item with validation"""
        if name:
            name = name.strip()
            if len(name) > 200:
                raise ValueError("Item name cannot exceed 200 characters")

            normalized_name = self.normalize_name(name)

            # Check for duplicates in same category
            existing = CategoryItem.query.filter(
                CategoryItem.category_id == self.category_id,
                CategoryItem.normalized_name == normalized_name,
                CategoryItem.id != self.id
            ).first()

            if existing:
                raise ValueError(f"Item '{name}' already exists in this category")

            self.name = name
            self.normalized_name = normalized_name

        if description is not None:
            self.description = description

        if keywords is not None:
            self.set_keywords_list(keywords)

        self.updated_at = datetime.now(timezone.utc)

    def get_keywords_list(self):
        """Get keywords as a list"""
        if self.keywords:
            import json
            try:
                return json.loads(self.keywords)
            except (json.JSONDecodeError, TypeError):
                return []
        return []

    def set_keywords_list(self, keywords_list):
        """Set keywords from a list with validation"""
        if keywords_list:
            import json
            # Clean and validate keywords
            clean_keywords = []
            for keyword in keywords_list:
                if isinstance(keyword, str) and keyword.strip():
                    clean_keywords.append(keyword.strip().lower())

            # Remove duplicates while preserving order
            seen = set()
            unique_keywords = []
            for keyword in clean_keywords:
                if keyword not in seen:
                    seen.add(keyword)
                    unique_keywords.append(keyword)

            self.keywords = json.dumps(unique_keywords) if unique_keywords else None
        else:
            self.keywords = None

    def increment_usage(self):
        """Increment usage count"""
        self.usage_count += 1
        self.updated_at = datetime.now(timezone.utc)

    def reset_usage(self):
        """Reset usage count to zero"""
        self.usage_count = 0
        self.updated_at = datetime.now(timezone.utc)

    def deactivate(self):
        """Deactivate this item"""
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)

    def reactivate(self):
        """Reactivate this item"""
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)

    def matches_text(self, text: str) -> bool:
        """Check if this item matches the given text"""
        if not text:
            return False

        text_lower = text.lower().strip()

        # Check direct name match
        if self.normalized_name in text_lower or text_lower in self.normalized_name:
            return True

        # Check keyword matches
        keywords = self.get_keywords_list()
        for keyword in keywords:
            if keyword in text_lower or text_lower in keyword:
                return True

        return False

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else None,
            'name': self.name,
            'normalized_name': self.normalized_name,
            'description': self.description,
            'keywords': self.get_keywords_list(),
            'is_active': self.is_active,
            'usage_count': self.usage_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

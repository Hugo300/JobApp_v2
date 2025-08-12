"""
Enhanced skill management service with flexible categorization
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from models import db, Category, CategoryItem, CategoryType
from .category_service import CategoryService
# Removed SkillCategorizationService - functionality moved to other services


class EnhancedSkillService:
    """Enhanced skill service with flexible categorization"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.category_service = CategoryService()
        # Legacy categorizer removed - using built-in categorization
    
    def initialize_skill_categories(self) -> bool:
        """Initialize comprehensive skill categories"""
        try:
            # Initialize default categories
            self.category_service.initialize_default_categories()

            # Create comprehensive skill categories
            self._create_comprehensive_categories()

            self.logger.info("Successfully initialized comprehensive skill categories")
            return True

        except Exception as e:
            self.logger.error(f"Error initializing skill categories: {str(e)}")
            return False

    def _create_comprehensive_categories(self):
        """Create comprehensive skill categories with detailed items"""
        try:
            # Define comprehensive skill categories with their items
            comprehensive_categories = {
                'Programming Languages': {
                    'description': 'Programming and scripting languages',
                    'color': '#e74c3c',
                    'icon': 'fas fa-code',
                    'items': [
                        ('Python', ['python', 'py', 'django', 'flask', 'fastapi']),
                        ('JavaScript', ['javascript', 'js', 'node.js', 'nodejs', 'typescript', 'ts']),
                        ('Java', ['java', 'spring', 'spring boot', 'maven', 'gradle']),
                        ('C#', ['c#', 'csharp', '.net', 'dotnet', 'asp.net']),
                        ('C++', ['c++', 'cpp', 'c plus plus']),
                        ('PHP', ['php', 'laravel', 'symfony', 'composer']),
                        ('Ruby', ['ruby', 'rails', 'ruby on rails', 'gem']),
                        ('Go', ['go', 'golang', 'go lang']),
                        ('Rust', ['rust', 'cargo']),
                        ('Swift', ['swift', 'ios', 'xcode']),
                        ('Kotlin', ['kotlin', 'android']),
                        ('Scala', ['scala', 'akka', 'play']),
                        ('R', ['r', 'rstudio', 'shiny']),
                        ('MATLAB', ['matlab', 'simulink']),
                        ('SQL', ['sql', 'mysql', 'postgresql', 'sqlite', 'oracle', 'mssql'])
                    ]
                },
                'Web Technologies': {
                    'description': 'Frontend and backend web development',
                    'color': '#3498db',
                    'icon': 'fas fa-globe',
                    'items': [
                        ('React', ['react', 'reactjs', 'jsx', 'redux', 'next.js']),
                        ('Angular', ['angular', 'angularjs', 'typescript']),
                        ('Vue.js', ['vue', 'vuejs', 'vue.js', 'vuex', 'nuxt']),
                        ('HTML', ['html', 'html5', 'markup']),
                        ('CSS', ['css', 'css3', 'sass', 'scss', 'less', 'stylus']),
                        ('Bootstrap', ['bootstrap', 'responsive design']),
                        ('Tailwind CSS', ['tailwind', 'tailwindcss', 'utility-first']),
                        ('jQuery', ['jquery', 'javascript library']),
                        ('Express.js', ['express', 'expressjs', 'node.js']),
                        ('Django', ['django', 'python', 'orm']),
                        ('Flask', ['flask', 'python', 'microframework']),
                        ('Laravel', ['laravel', 'php', 'eloquent']),
                        ('Spring Boot', ['spring boot', 'spring', 'java']),
                        ('ASP.NET', ['asp.net', 'c#', 'mvc'])
                    ]
                },
                'Databases': {
                    'description': 'Database management systems',
                    'color': '#9b59b6',
                    'icon': 'fas fa-database',
                    'items': [
                        ('MySQL', ['mysql', 'mariadb', 'relational']),
                        ('PostgreSQL', ['postgresql', 'postgres', 'psql']),
                        ('MongoDB', ['mongodb', 'mongo', 'nosql', 'document']),
                        ('Redis', ['redis', 'cache', 'in-memory']),
                        ('Elasticsearch', ['elasticsearch', 'elastic', 'search']),
                        ('SQLite', ['sqlite', 'embedded']),
                        ('Oracle', ['oracle', 'plsql', 'enterprise']),
                        ('Microsoft SQL Server', ['mssql', 'sql server', 'tsql']),
                        ('Cassandra', ['cassandra', 'distributed', 'nosql']),
                        ('DynamoDB', ['dynamodb', 'aws', 'nosql']),
                        ('Firebase', ['firebase', 'firestore', 'realtime'])
                    ]
                },
                'Cloud & DevOps': {
                    'description': 'Cloud platforms and DevOps tools',
                    'color': '#f39c12',
                    'icon': 'fas fa-cloud',
                    'items': [
                        ('AWS', ['aws', 'amazon web services', 'ec2', 's3', 'lambda']),
                        ('Azure', ['azure', 'microsoft azure', 'azure devops']),
                        ('Google Cloud', ['gcp', 'google cloud', 'google cloud platform']),
                        ('Docker', ['docker', 'containerization', 'containers']),
                        ('Kubernetes', ['kubernetes', 'k8s', 'orchestration']),
                        ('Jenkins', ['jenkins', 'ci/cd', 'automation']),
                        ('Git', ['git', 'github', 'gitlab', 'version control']),
                        ('Terraform', ['terraform', 'infrastructure as code', 'iac']),
                        ('Ansible', ['ansible', 'configuration management']),
                        ('Nginx', ['nginx', 'web server', 'reverse proxy']),
                        ('Apache', ['apache', 'httpd', 'web server'])
                    ]
                }
            }

            # Create categories and their items
            for category_name, category_data in comprehensive_categories.items():
                category = self._get_or_create_enhanced_category(
                    category_name,
                    category_data['description'],
                    category_data['color'],
                    category_data['icon']
                )

                if category:
                    self._populate_category_with_items(category.id, category_data['items'])

        except Exception as e:
            self.logger.error(f"Error creating comprehensive categories: {str(e)}")
    
    def _get_or_create_enhanced_category(self, name: str, description: str, color: str, icon: str) -> Optional[Category]:
        """Get or create an enhanced skill category with visual styling"""
        try:
            # Try to find existing category
            category = Category.query.filter_by(
                name=name,
                category_type=CategoryType.SKILL.value
            ).first()

            if category:
                # Update existing category with new styling if needed
                if category.color != color or category.icon != icon:
                    category.color = color
                    category.icon = icon
                    category.description = description
                    db.session.commit()
                return category

            # Create new category
            success, category, error = self.category_service.create_category(
                name=name,
                category_type=CategoryType.SKILL.value,
                description=description,
                color=color,
                icon=icon,
                is_system=True
            )

            return category if success else None

        except Exception as e:
            self.logger.error(f"Error getting/creating enhanced skill category {name}: {str(e)}")
            return None

    def _populate_category_with_items(self, category_id: int, items_data: List[Tuple[str, List[str]]]):
        """Populate category with skill items and their keywords"""
        try:
            created_count = 0
            for item_name, keywords in items_data:
                # Check if item already exists
                existing_item = CategoryItem.query.filter_by(
                    category_id=category_id,
                    normalized_name=CategoryItem.normalize_name(item_name)
                ).first()

                if not existing_item:
                    success, item, error = self.category_service.create_category_item(
                        category_id=category_id,
                        name=item_name,
                        keywords=keywords
                    )

                    if success:
                        created_count += 1
                    else:
                        self.logger.warning(f"Failed to create item {item_name}: {error}")
                else:
                    # Update keywords if needed
                    existing_keywords = set(existing_item.get_keywords_list())
                    new_keywords = set([k.lower() for k in keywords])
                    if not new_keywords.issubset(existing_keywords):
                        combined_keywords = list(existing_keywords.union(new_keywords))
                        existing_item.set_keywords_list(combined_keywords)
                        db.session.commit()

            if created_count > 0:
                self.logger.info(f"Created {created_count} new items in category {category_id}")

        except Exception as e:
            self.logger.error(f"Error populating category {category_id}: {str(e)}")

    def _get_or_create_skill_category(self, name: str, description: str) -> Optional[Category]:
        """Get or create a basic skill category (legacy method)"""
        try:
            # Try to find existing category
            category = Category.query.filter_by(
                name=name,
                category_type=CategoryType.SKILL.value
            ).first()

            if category:
                return category

            # Create new category
            success, category, error = self.category_service.create_category(
                name=name,
                category_type=CategoryType.SKILL.value,
                description=description,
                is_system=True
            )

            return category if success else None

        except Exception as e:
            self.logger.error(f"Error getting/creating skill category {name}: {str(e)}")
            return None
    
    def _populate_category_from_legacy(self, category_id: int, legacy_skills: set, skill_type: str):
        """Populate category with legacy skills"""
        try:
            created_count = 0
            for skill in legacy_skills:
                success, item, error = self.category_service.create_category_item(
                    category_id=category_id,
                    name=skill.title(),
                    description=f"Legacy {skill_type} skill",
                    keywords=[skill, skill.lower(), skill.upper()]
                )
                if success:
                    created_count += 1
                elif "already exists" not in (error or ""):
                    self.logger.debug(f"Could not create skill item {skill}: {error}")
            
            self.logger.info(f"Created {created_count} {skill_type} skill items")
            
        except Exception as e:
            self.logger.error(f"Error populating category from legacy skills: {str(e)}")
    
    def categorize_skills_enhanced(self, skills: List[str], user_skills: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Enhanced skill categorization using flexible categories
        
        Args:
            skills: List of skills to categorize
            user_skills: Optional list of user skills for matching
            
        Returns:
            Dictionary with categorized skills and metadata
        """
        try:
            if not skills:
                return {
                    'hard_skills': {'matched': [], 'unmatched': []},
                    'soft_skills': {'matched': [], 'unmatched': []},
                    'other_skills': {'matched': [], 'unmatched': []},
                    'categories': {},
                    'total_skills': 0,
                    'match_score': 0
                }
            
            # Get skill categories
            skill_categories = self.category_service.get_categories_by_type(CategoryType.SKILL.value)
            
            categorized_skills = {}
            all_matched = []
            all_unmatched = []
            
            # Initialize category results
            for category in skill_categories:
                categorized_skills[category.name.lower().replace(' ', '_')] = {
                    'matched': [],
                    'unmatched': [],
                    'category_info': {
                        'id': category.id,
                        'name': category.name,
                        'color': category.color,
                        'icon': category.icon
                    }
                }
            
            # Categorize each skill
            for skill in skills:
                categorized = False
                is_matched = self._is_skill_matched(skill, user_skills)
                
                # Try to match against each category
                for category in skill_categories:
                    if self._skill_belongs_to_category(skill, category):
                        category_key = category.name.lower().replace(' ', '_')
                        if is_matched:
                            categorized_skills[category_key]['matched'].append(skill)
                            all_matched.append(skill)
                        else:
                            categorized_skills[category_key]['unmatched'].append(skill)
                            all_unmatched.append(skill)
                        categorized = True
                        break
                
                # If not categorized, put in "other"
                if not categorized:
                    if 'other_skills' not in categorized_skills:
                        categorized_skills['other_skills'] = {
                            'matched': [],
                            'unmatched': [],
                            'category_info': {
                                'name': 'Other Skills',
                                'color': '#6c757d',
                                'icon': 'fas fa-tag'
                            }
                        }
                    
                    if is_matched:
                        categorized_skills['other_skills']['matched'].append(skill)
                        all_matched.append(skill)
                    else:
                        categorized_skills['other_skills']['unmatched'].append(skill)
                        all_unmatched.append(skill)
            
            # Calculate match score
            total_skills = len(skills)
            match_score = (len(all_matched) / total_skills * 100) if total_skills > 0 else 0
            
            # Maintain backward compatibility
            result = {
                'hard_skills': categorized_skills.get('hard_skills', {'matched': [], 'unmatched': []}),
                'soft_skills': categorized_skills.get('soft_skills', {'matched': [], 'unmatched': []}),
                'other_skills': categorized_skills.get('other_skills', {'matched': [], 'unmatched': []}),
                'categories': categorized_skills,
                'total_skills': total_skills,
                'match_score': round(match_score, 1),
                'matched_skills': all_matched,
                'unmatched_skills': all_unmatched
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error in enhanced skill categorization: {str(e)}")
            # Fallback to legacy categorization
            return self._fallback_categorization(skills, user_skills)
    
    def _skill_belongs_to_category(self, skill: str, category: Category) -> bool:
        """Check if a skill belongs to a category using enhanced fuzzy matching"""
        try:
            # Get category items
            items = self.category_service.get_category_items(category.id)

            skill_lower = skill.lower().strip()
            skill_words = set(skill_lower.split())

            for item in items:
                # Check direct name match
                if item.normalized_name == skill_lower:
                    item.increment_usage()
                    db.session.commit()
                    return True

                # Check partial name match
                if item.normalized_name in skill_lower or skill_lower in item.normalized_name:
                    item.increment_usage()
                    db.session.commit()
                    return True

                # Check keyword matches with enhanced fuzzy logic
                keywords = item.get_keywords_list()
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    keyword_words = set(keyword_lower.split())

                    # Exact keyword match
                    if keyword_lower == skill_lower:
                        item.increment_usage()
                        db.session.commit()
                        return True

                    # Partial keyword match
                    if keyword_lower in skill_lower or skill_lower in keyword_lower:
                        item.increment_usage()
                        db.session.commit()
                        return True

                    # Word-based fuzzy matching for compound skills
                    if skill_words and keyword_words:
                        intersection = skill_words.intersection(keyword_words)
                        # Match if at least 60% of words overlap
                        min_words = min(len(skill_words), len(keyword_words))
                        if min_words > 0 and len(intersection) >= min_words * 0.6:
                            item.increment_usage()
                            db.session.commit()
                            return True

                    # Check for common abbreviations and variations
                    if self._check_skill_variations(skill_lower, keyword_lower):
                        item.increment_usage()
                        db.session.commit()
                        return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking skill category membership: {str(e)}")
            return False

    def _check_skill_variations(self, skill: str, keyword: str) -> bool:
        """Check for common skill variations and abbreviations"""
        try:
            # Common variations mapping
            variations = {
                'js': 'javascript',
                'ts': 'typescript',
                'py': 'python',
                'cpp': 'c++',
                'cs': 'c#',
                'db': 'database',
                'api': 'application programming interface',
                'ui': 'user interface',
                'ux': 'user experience',
                'ml': 'machine learning',
                'ai': 'artificial intelligence',
                'aws': 'amazon web services',
                'gcp': 'google cloud platform',
                'k8s': 'kubernetes',
                'ci/cd': 'continuous integration continuous deployment'
            }

            # Check if skill is an abbreviation of keyword or vice versa
            if skill in variations and variations[skill] in keyword:
                return True
            if keyword in variations and variations[keyword] in skill:
                return True

            # Check reverse mapping
            reverse_variations = {v: k for k, v in variations.items()}
            if skill in reverse_variations and reverse_variations[skill] in keyword:
                return True
            if keyword in reverse_variations and reverse_variations[keyword] in skill:
                return True

            return False

        except Exception as e:
            self.logger.error(f"Error checking skill variations: {str(e)}")
            return False
    
    def _is_skill_matched(self, skill: str, user_skills: Optional[List[str]]) -> bool:
        """Check if skill is matched against user skills"""
        if not user_skills:
            return False
        
        skill_lower = skill.lower().strip()
        user_skills_lower = [s.lower().strip() for s in user_skills]
        
        return skill_lower in user_skills_lower
    
    def _fallback_categorization(self, skills: List[str], user_skills: Optional[List[str]]) -> Dict[str, Any]:
        """Simple categorization without legacy service"""
        try:
            from utils.skill_constants import is_soft_skill

            user_skills_lower = [skill.lower() for skill in (user_skills or [])]
            hard_skills_matched = []
            hard_skills_unmatched = []
            soft_skills_matched = []
            soft_skills_unmatched = []
            other_skills_matched = []
            other_skills_unmatched = []

            for skill in skills:
                skill_lower = skill.lower()
                is_matched = skill_lower in user_skills_lower

                if is_soft_skill(skill):
                    if is_matched:
                        soft_skills_matched.append(skill)
                    else:
                        soft_skills_unmatched.append(skill)
                else:
                    # Treat as hard skill by default
                    if is_matched:
                        hard_skills_matched.append(skill)
                    else:
                        hard_skills_unmatched.append(skill)

            matched_skills = hard_skills_matched + soft_skills_matched + other_skills_matched
            unmatched_skills = hard_skills_unmatched + soft_skills_unmatched + other_skills_unmatched
            match_score = len(matched_skills) / len(skills) if skills else 0

            return {
                'hard_skills': {
                    'matched': hard_skills_matched,
                    'unmatched': hard_skills_unmatched
                },
                'soft_skills': {
                    'matched': soft_skills_matched,
                    'unmatched': soft_skills_unmatched
                },
                'other_skills': {
                    'matched': other_skills_matched,
                    'unmatched': other_skills_unmatched
                },
                'categories': {},
                'total_skills': len(skills),
                'match_score': match_score,
                'matched_skills': matched_skills,
                'unmatched_skills': unmatched_skills
            }

        except Exception as e:
            self.logger.error(f"Error in fallback categorization: {str(e)}")
            return {
                'hard_skills': {'matched': [], 'unmatched': []},
                'soft_skills': {'matched': [], 'unmatched': []},
                'other_skills': {'matched': [], 'unmatched': skills},
                'categories': {},
                'total_skills': len(skills),
                'match_score': 0,
                'matched_skills': [],
                'unmatched_skills': skills
            }
    
    def add_skill_to_category(self, skill_name: str, category_name: str, 
                             keywords: Optional[List[str]] = None) -> Tuple[bool, Optional[str]]:
        """Add a skill to a specific category"""
        try:
            # Find category
            category = Category.query.filter_by(
                name=category_name,
                category_type=CategoryType.SKILL.value
            ).first()
            
            if not category:
                return False, f"Category '{category_name}' not found"
            
            # Create category item
            success, item, error = self.category_service.create_category_item(
                category_id=category.id,
                name=skill_name,
                keywords=keywords or [skill_name.lower()]
            )
            
            return success, error
            
        except Exception as e:
            self.logger.error(f"Error adding skill to category: {str(e)}")
            return False, str(e)
    
    def get_skill_statistics(self) -> Dict[str, Any]:
        """Get statistics about skills and categories"""
        try:
            skill_categories = self.category_service.get_categories_by_type(CategoryType.SKILL.value)
            
            stats = {
                'total_categories': len(skill_categories),
                'categories': {},
                'total_skills': 0,
                'most_used_skills': []
            }
            
            for category in skill_categories:
                items = self.category_service.get_category_items(category.id)
                stats['categories'][category.name] = {
                    'count': len(items),
                    'color': category.color,
                    'icon': category.icon
                }
                stats['total_skills'] += len(items)
            
            # Get most used skills
            most_used = CategoryItem.query.join(Category).filter(
                Category.category_type == CategoryType.SKILL.value
            ).order_by(CategoryItem.usage_count.desc()).limit(10).all()
            
            stats['most_used_skills'] = [
                {
                    'name': item.name,
                    'category': item.category.name,
                    'usage_count': item.usage_count
                }
                for item in most_used
            ]
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting skill statistics: {str(e)}")
            return {
                'total_categories': 0,
                'categories': {},
                'total_skills': 0,
                'most_used_skills': []
            }

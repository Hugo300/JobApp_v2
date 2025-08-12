"""
Industry management service for job categorization
"""
import logging
from typing import List, Dict, Optional, Tuple, Any
from models import db, Category, CategoryItem, CategoryType, JobApplication
from .category_service import CategoryService
from .database_service import db_service


class IndustryService:
    """Service for managing job industries"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.category_service = CategoryService()
    
    def initialize_default_industries(self) -> bool:
        """Initialize default industry categories"""
        try:
            # Get or create industries category
            industries_cat = self._get_or_create_industries_category()
            if not industries_cat:
                return False
            
            # Default industries with keywords
            default_industries = [
                {
                    'name': 'Technology',
                    'keywords': ['tech', 'software', 'it', 'computer', 'digital', 'saas', 'fintech', 'edtech']
                },
                {
                    'name': 'Healthcare',
                    'keywords': ['health', 'medical', 'hospital', 'pharmaceutical', 'biotech', 'healthcare']
                },
                {
                    'name': 'Finance',
                    'keywords': ['finance', 'banking', 'investment', 'insurance', 'financial services', 'fintech']
                },
                {
                    'name': 'Education',
                    'keywords': ['education', 'school', 'university', 'learning', 'training', 'edtech']
                },
                {
                    'name': 'Manufacturing',
                    'keywords': ['manufacturing', 'production', 'factory', 'industrial', 'automotive']
                },
                {
                    'name': 'Retail',
                    'keywords': ['retail', 'ecommerce', 'shopping', 'consumer', 'merchandise']
                },
                {
                    'name': 'Consulting',
                    'keywords': ['consulting', 'advisory', 'professional services', 'strategy']
                },
                {
                    'name': 'Media & Entertainment',
                    'keywords': ['media', 'entertainment', 'gaming', 'publishing', 'broadcasting']
                },
                {
                    'name': 'Real Estate',
                    'keywords': ['real estate', 'property', 'construction', 'architecture']
                },
                {
                    'name': 'Transportation',
                    'keywords': ['transportation', 'logistics', 'shipping', 'delivery', 'automotive']
                },
                {
                    'name': 'Energy',
                    'keywords': ['energy', 'oil', 'gas', 'renewable', 'utilities', 'power']
                },
                {
                    'name': 'Government',
                    'keywords': ['government', 'public sector', 'federal', 'state', 'municipal']
                },
                {
                    'name': 'Non-Profit',
                    'keywords': ['non-profit', 'nonprofit', 'ngo', 'charity', 'foundation']
                },
                {
                    'name': 'Telecommunications',
                    'keywords': ['telecom', 'telecommunications', 'wireless', 'network', 'communications']
                },
                {
                    'name': 'Agriculture',
                    'keywords': ['agriculture', 'farming', 'food', 'agtech', 'agricultural']
                }
            ]
            
            created_count = 0
            for industry_data in default_industries:
                success, item, error = self.category_service.create_category_item(
                    category_id=industries_cat.id,
                    name=industry_data['name'],
                    description=f"{industry_data['name']} industry",
                    keywords=industry_data['keywords']
                )
                if success:
                    created_count += 1
                elif "already exists" not in (error or ""):
                    self.logger.warning(f"Failed to create industry {industry_data['name']}: {error}")
            
            self.logger.info(f"Initialized {created_count} default industries")
            return True
            
        except Exception as e:
            self.logger.error(f"Error initializing default industries: {str(e)}")
            return False
    
    def _get_or_create_industries_category(self) -> Optional[Category]:
        """Get or create the industries category"""
        try:
            # Try to find existing category
            category = Category.query.filter_by(
                name='Industries',
                category_type=CategoryType.INDUSTRY.value
            ).first()
            
            if category:
                return category
            
            # Create new category
            success, category, error = self.category_service.create_category(
                name='Industries',
                category_type=CategoryType.INDUSTRY.value,
                description='Industry classifications for jobs',
                is_system=True
            )
            
            return category if success else None
            
        except Exception as e:
            self.logger.error(f"Error getting/creating industries category: {str(e)}")
            return None
    
    def detect_job_industry(self, job_title: str, company_name: str, 
                           job_description: Optional[str] = None) -> Optional[CategoryItem]:
        """
        Detect industry for a job based on title, company, and description
        
        Args:
            job_title: Job title
            company_name: Company name
            job_description: Optional job description
            
        Returns:
            CategoryItem: Detected industry or None
        """
        try:
            # Combine all text for analysis
            text_parts = [job_title, company_name]
            if job_description:
                text_parts.append(job_description)
            
            combined_text = ' '.join(text_parts).lower()
            
            # Get all industries
            industries = self.get_all_industries()
            
            # Score each industry
            industry_scores = []
            for industry in industries:
                score = self._calculate_industry_score(industry, combined_text)
                if score > 0:
                    industry_scores.append((industry, score))
            
            # Return the highest scoring industry
            if industry_scores:
                industry_scores.sort(key=lambda x: x[1], reverse=True)
                best_industry = industry_scores[0][0]
                
                # Increment usage count
                best_industry.increment_usage()
                db.session.commit()
                
                return best_industry
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error detecting job industry: {str(e)}")
            return None
    
    def _calculate_industry_score(self, industry: CategoryItem, text: str) -> float:
        """Calculate how well an industry matches the given text"""
        try:
            score = 0.0
            
            # Check industry name
            if industry.normalized_name in text:
                score += 10.0
            
            # Check keywords
            keywords = industry.get_keywords_list()
            for keyword in keywords:
                if keyword.lower() in text:
                    # Weight longer keywords higher
                    score += len(keyword.split()) * 2.0
            
            return score
            
        except Exception as e:
            self.logger.error(f"Error calculating industry score: {str(e)}")
            return 0.0
    
    def get_all_industries(self, active_only: bool = True) -> List[CategoryItem]:
        """Get all industry items"""
        try:
            industries_cat = Category.query.filter_by(
                name='Industries',
                category_type=CategoryType.INDUSTRY.value
            ).first()
            
            if not industries_cat:
                return []
            
            return self.category_service.get_category_items(industries_cat.id, active_only)
            
        except Exception as e:
            self.logger.error(f"Error getting all industries: {str(e)}")
            return []
    
    def assign_industry_to_job(self, job_id: int, industry_id: int) -> Tuple[bool, Optional[str]]:
        """Assign an industry to a job"""
        try:
            # Get job
            job = db.session.get(JobApplication, job_id)
            if not job:
                return False, "Job not found"

            # Get industry
            industry = db.session.get(CategoryItem, industry_id)
            if not industry:
                return False, "Industry not found"
            
            # Verify industry is actually an industry
            if industry.category.category_type != CategoryType.INDUSTRY.value:
                return False, "Selected item is not an industry"
            
            # Assign industry
            job.industry_id = industry_id
            db.session.commit()
            
            # Increment usage count
            industry.increment_usage()
            db.session.commit()
            
            self.logger.info(f"Assigned industry {industry.name} to job {job.title} at {job.company}")
            return True, None
            
        except Exception as e:
            self.logger.error(f"Error assigning industry to job: {str(e)}")
            return False, str(e)
    
    def auto_assign_industries_to_jobs(self, limit: int = 100) -> Dict[str, int]:
        """Auto-assign industries to jobs that don't have one"""
        try:
            # Get jobs without industry
            jobs = JobApplication.query.filter_by(industry_id=None).limit(limit).all()
            
            assigned_count = 0
            skipped_count = 0
            
            for job in jobs:
                detected_industry = self.detect_job_industry(
                    job.title,
                    job.company,
                    job.description
                )
                
                if detected_industry:
                    job.industry_id = detected_industry.id
                    assigned_count += 1
                else:
                    skipped_count += 1
            
            if assigned_count > 0:
                db.session.commit()
            
            self.logger.info(f"Auto-assigned industries: {assigned_count} assigned, {skipped_count} skipped")
            
            return {
                'assigned': assigned_count,
                'skipped': skipped_count,
                'total_processed': len(jobs)
            }
            
        except Exception as e:
            self.logger.error(f"Error auto-assigning industries: {str(e)}")
            return {'assigned': 0, 'skipped': 0, 'total_processed': 0}
    
    def get_industry_statistics(self) -> Dict[str, Any]:
        """Get statistics about industries"""
        try:
            industries = self.get_all_industries()
            
            # Get job counts per industry
            industry_stats = []
            for industry in industries:
                job_count = JobApplication.query.filter_by(industry_id=industry.id).count()
                industry_stats.append({
                    'id': industry.id,
                    'name': industry.name,
                    'job_count': job_count,
                    'usage_count': industry.usage_count
                })
            
            # Sort by job count
            industry_stats.sort(key=lambda x: x['job_count'], reverse=True)
            
            # Calculate totals
            total_jobs = JobApplication.query.count()
            jobs_with_industry = JobApplication.query.filter(JobApplication.industry_id.isnot(None)).count()
            jobs_without_industry = total_jobs - jobs_with_industry
            
            return {
                'total_industries': len(industries),
                'total_jobs': total_jobs,
                'jobs_with_industry': jobs_with_industry,
                'jobs_without_industry': jobs_without_industry,
                'coverage_percentage': round((jobs_with_industry / total_jobs * 100) if total_jobs > 0 else 0, 1),
                'industry_breakdown': industry_stats[:10],  # Top 10
                'top_industries': [stat for stat in industry_stats[:5] if stat['job_count'] > 0]
            }
            
        except Exception as e:
            self.logger.error(f"Error getting industry statistics: {str(e)}")
            return {
                'total_industries': 0,
                'total_jobs': 0,
                'jobs_with_industry': 0,
                'jobs_without_industry': 0,
                'coverage_percentage': 0,
                'industry_breakdown': [],
                'top_industries': []
            }

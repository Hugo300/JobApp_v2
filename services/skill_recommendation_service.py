"""
Skill Recommendation Service

Provides intelligent skill recommendations based on:
- Job market trends
- User's current skills
- Career goals and paths
- Industry demands
- Skill complementarity
"""

import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
from models import db, JobApplication, Category, CategoryItem, CategoryType, UserData
from services.skill_analytics_service import SkillAnalyticsService
from services.skill_extraction_service import SkillExtractionService
from services.base_service import BaseService, SkillServiceMixin
from utils.skill_constants import SKILL_RELATIONSHIPS, CAREER_PATHS


class SkillRecommendationService(BaseService, SkillServiceMixin):
    """Service for providing intelligent skill recommendations"""

    def __init__(self):
        super().__init__("SkillRecommendation")
        self.analytics_service = SkillAnalyticsService()
        self.extraction_service = SkillExtractionService()
        self._skill_relationships = SKILL_RELATIONSHIPS
        self._career_paths = CAREER_PATHS
    

    
    def get_skill_recommendations(self, user_skills: List[str], target_role: Optional[str] = None, 
                                 limit: int = 10) -> Dict[str, Any]:
        """
        Get personalized skill recommendations
        
        Args:
            user_skills: List of user's current skills
            target_role: Target career role (optional)
            limit: Maximum number of recommendations
            
        Returns:
            Dictionary with recommendations and reasoning
        """
        try:
            recommendations = []
            
            # Get market trend recommendations
            trend_recs = self._get_trend_based_recommendations(user_skills)
            recommendations.extend(trend_recs)
            
            # Get complementary skill recommendations
            comp_recs = self._get_complementary_recommendations(user_skills)
            recommendations.extend(comp_recs)
            
            # Get career path recommendations if target role specified
            if target_role:
                career_recs = self._get_career_path_recommendations(user_skills, target_role)
                recommendations.extend(career_recs)
            
            # Get gap analysis recommendations
            gap_recs = self._get_gap_analysis_recommendations(user_skills)
            recommendations.extend(gap_recs)
            
            # Score and rank recommendations
            scored_recs = self._score_recommendations(recommendations, user_skills)
            
            # Remove duplicates and limit results
            final_recs = self._deduplicate_recommendations(scored_recs)[:limit]
            
            return {
                'success': True,
                'recommendations': final_recs,
                'user_skills_count': len(user_skills),
                'target_role': target_role,
                'recommendation_sources': {
                    'market_trends': len(trend_recs),
                    'complementary': len(comp_recs),
                    'career_path': len(career_recs) if target_role else 0,
                    'gap_analysis': len(gap_recs)
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error getting skill recommendations: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'recommendations': []
            }
    
    def _get_trend_based_recommendations(self, user_skills: List[str]) -> List[Dict[str, Any]]:
        """Get recommendations based on market trends"""
        try:
            # Get trending skills from analytics
            trends = self.analytics_service.get_trending_skills(30, 60)
            if 'error' in trends:
                return []
            
            recommendations = []
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            # Recommend rising skills that user doesn't have
            for skill_data in trends.get('trending_up', [])[:5]:
                skill = skill_data['skill']
                if skill.lower() not in user_skills_lower:
                    recommendations.append({
                        'skill': skill,
                        'reason': f"Trending up {skill_data['growth_rate']}% in recent job postings",
                        'source': 'market_trends',
                        'priority': 'high' if skill_data['growth_rate'] > 50 else 'medium',
                        'category': skill_data.get('category', {}).get('name', 'Other'),
                        'growth_rate': skill_data['growth_rate']
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting trend-based recommendations: {str(e)}")
            return []
    
    def _get_complementary_recommendations(self, user_skills: List[str]) -> List[Dict[str, Any]]:
        """Get recommendations for complementary skills"""
        try:
            recommendations = []
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            # Find complementary skills based on relationships
            for user_skill in user_skills:
                skill_lower = user_skill.lower()
                if skill_lower in self._skill_relationships:
                    related_skills = self._skill_relationships[skill_lower]
                    
                    for related_skill in related_skills:
                        if related_skill.lower() not in user_skills_lower:
                            recommendations.append({
                                'skill': related_skill,
                                'reason': f"Commonly used with {user_skill}",
                                'source': 'complementary',
                                'priority': 'medium',
                                'related_to': user_skill,
                                'category': self._get_skill_category(related_skill)
                            })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting complementary recommendations: {str(e)}")
            return []
    
    def _get_career_path_recommendations(self, user_skills: List[str], target_role: str) -> List[Dict[str, Any]]:
        """Get recommendations based on career path"""
        try:
            recommendations = []
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            if target_role not in self._career_paths:
                return recommendations
            
            path_data = self._career_paths[target_role]
            
            # Check core skills
            for skill in path_data['core_skills']:
                if skill.lower() not in user_skills_lower:
                    recommendations.append({
                        'skill': skill,
                        'reason': f"Core skill for {target_role}",
                        'source': 'career_path',
                        'priority': 'high',
                        'skill_level': 'core',
                        'target_role': target_role,
                        'category': self._get_skill_category(skill)
                    })
            
            # Check recommended skills
            for skill in path_data['recommended_skills']:
                if skill.lower() not in user_skills_lower:
                    recommendations.append({
                        'skill': skill,
                        'reason': f"Recommended for {target_role}",
                        'source': 'career_path',
                        'priority': 'medium',
                        'skill_level': 'recommended',
                        'target_role': target_role,
                        'category': self._get_skill_category(skill)
                    })
            
            # Check advanced skills (lower priority)
            for skill in path_data['advanced_skills']:
                if skill.lower() not in user_skills_lower:
                    recommendations.append({
                        'skill': skill,
                        'reason': f"Advanced skill for {target_role}",
                        'source': 'career_path',
                        'priority': 'low',
                        'skill_level': 'advanced',
                        'target_role': target_role,
                        'category': self._get_skill_category(skill)
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting career path recommendations: {str(e)}")
            return []
    
    def _get_gap_analysis_recommendations(self, user_skills: List[str]) -> List[Dict[str, Any]]:
        """Get recommendations based on skill gap analysis"""
        try:
            recommendations = []
            
            # Get performance metrics to identify high-performing skills
            performance = self.analytics_service.get_skill_performance_metrics()
            if 'error' in performance:
                return recommendations
            
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            # Recommend top-performing skills that user doesn't have
            for skill_data in performance.get('top_performing_skills', [])[:5]:
                skill = skill_data['skill']
                if skill.lower() not in user_skills_lower:
                    recommendations.append({
                        'skill': skill,
                        'reason': f"High success rate ({skill_data['success_rate']}%) in job applications",
                        'source': 'gap_analysis',
                        'priority': 'high' if skill_data['success_rate'] > 80 else 'medium',
                        'success_rate': skill_data['success_rate'],
                        'category': skill_data.get('category', {}).get('name', 'Other')
                    })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error getting gap analysis recommendations: {str(e)}")
            return []
    
    def _score_recommendations(self, recommendations: List[Dict[str, Any]], user_skills: List[str]) -> List[Dict[str, Any]]:
        """Score recommendations based on various factors"""
        try:
            for rec in recommendations:
                score = 0
                
                # Priority scoring
                if rec.get('priority') == 'high':
                    score += 10
                elif rec.get('priority') == 'medium':
                    score += 5
                else:
                    score += 1
                
                # Source scoring
                source_scores = {
                    'career_path': 8,
                    'market_trends': 6,
                    'gap_analysis': 7,
                    'complementary': 4
                }
                score += source_scores.get(rec.get('source', ''), 0)
                
                # Growth rate bonus
                if 'growth_rate' in rec and rec['growth_rate'] > 30:
                    score += 3
                
                # Success rate bonus
                if 'success_rate' in rec and rec['success_rate'] > 75:
                    score += 3
                
                rec['score'] = score
            
            # Sort by score descending
            return sorted(recommendations, key=lambda x: x.get('score', 0), reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error scoring recommendations: {str(e)}")
            return recommendations
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate recommendations, keeping the highest scored"""
        seen_skills = set()
        unique_recs = []
        
        for rec in recommendations:
            skill_lower = rec['skill'].lower()
            if skill_lower not in seen_skills:
                seen_skills.add(skill_lower)
                unique_recs.append(rec)
        
        return unique_recs
    
    def _get_skill_category(self, skill: str) -> str:
        """Get category name for a skill"""
        try:
            # Simple categorization based on skill name
            skill_lower = skill.lower()
            
            programming_langs = ['python', 'javascript', 'java', 'c#', 'c++', 'php', 'ruby', 'go', 'rust']
            web_tech = ['react', 'angular', 'vue', 'html', 'css', 'node.js', 'express']
            cloud_devops = ['aws', 'azure', 'docker', 'kubernetes', 'terraform', 'jenkins']
            databases = ['sql', 'mysql', 'postgresql', 'mongodb', 'redis']
            
            if any(lang in skill_lower for lang in programming_langs):
                return 'Programming Languages'
            elif any(tech in skill_lower for tech in web_tech):
                return 'Web Technologies'
            elif any(tool in skill_lower for tool in cloud_devops):
                return 'Cloud & DevOps'
            elif any(db in skill_lower for db in databases):
                return 'Databases'
            else:
                return 'Other Technical'
                
        except Exception as e:
            self.logger.error(f"Error getting skill category: {str(e)}")
            return 'Other'
    
    def get_career_path_analysis(self, user_skills: List[str]) -> Dict[str, Any]:
        """Analyze user's skills against different career paths"""
        try:
            analysis = {}
            user_skills_lower = [skill.lower() for skill in user_skills]
            
            for role, path_data in self._career_paths.items():
                # Calculate skill coverage for each level
                core_coverage = sum(1 for skill in path_data['core_skills'] 
                                  if skill.lower() in user_skills_lower)
                core_total = len(path_data['core_skills'])
                
                rec_coverage = sum(1 for skill in path_data['recommended_skills'] 
                                 if skill.lower() in user_skills_lower)
                rec_total = len(path_data['recommended_skills'])
                
                adv_coverage = sum(1 for skill in path_data['advanced_skills'] 
                                 if skill.lower() in user_skills_lower)
                adv_total = len(path_data['advanced_skills'])
                
                # Calculate overall readiness score
                core_score = (core_coverage / core_total) * 60  # 60% weight for core skills
                rec_score = (rec_coverage / rec_total) * 30    # 30% weight for recommended
                adv_score = (adv_coverage / adv_total) * 10    # 10% weight for advanced
                
                readiness_score = core_score + rec_score + adv_score
                
                analysis[role] = {
                    'readiness_score': round(readiness_score, 1),
                    'core_skills': {
                        'covered': core_coverage,
                        'total': core_total,
                        'percentage': round((core_coverage / core_total) * 100, 1)
                    },
                    'recommended_skills': {
                        'covered': rec_coverage,
                        'total': rec_total,
                        'percentage': round((rec_coverage / rec_total) * 100, 1)
                    },
                    'advanced_skills': {
                        'covered': adv_coverage,
                        'total': adv_total,
                        'percentage': round((adv_coverage / adv_total) * 100, 1)
                    },
                    'missing_core_skills': [skill for skill in path_data['core_skills'] 
                                          if skill.lower() not in user_skills_lower]
                }
            
            # Sort by readiness score
            sorted_analysis = dict(sorted(analysis.items(), 
                                        key=lambda x: x[1]['readiness_score'], 
                                        reverse=True))
            
            return {
                'success': True,
                'career_paths': sorted_analysis,
                'user_skills_count': len(user_skills)
            }
            
        except Exception as e:
            self.logger.error(f"Error in career path analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

"""
Skill Gap Analysis Service

Provides comprehensive skill gap analysis including:
- Gap identification between user skills and job requirements
- Learning path recommendations
- Priority-based skill development suggestions
- Progress tracking and milestones
"""

import logging
from typing import Dict, List, Set, Any, Optional, Tuple
from collections import defaultdict, Counter
from datetime import datetime, timedelta, timezone
from models import db, JobApplication, UserData
from services.skill_extraction_service import SkillExtractionService
from services.skill_recommendation_service import SkillRecommendationService
from services.skill_matching_service import SkillMatchingService
from services.base_service import BaseService, SkillServiceMixin
from utils.skill_constants import SKILL_DIFFICULTY, LEARNING_RESOURCES


class SkillGapAnalysisService(BaseService, SkillServiceMixin):
    """Service for analyzing skill gaps and providing learning recommendations"""

    def __init__(self):
        super().__init__("SkillGapAnalysis")
        self.extraction_service = SkillExtractionService()
        self.recommendation_service = SkillRecommendationService()
        self.matching_service = SkillMatchingService()
        self._learning_resources = LEARNING_RESOURCES
        self._skill_difficulty = SKILL_DIFFICULTY
    
    def _initialize_learning_data(self):
        """Initialize learning resources and skill difficulty data"""
        try:
            # Define learning resources for different skills
            self._learning_resources = {
                'python': {
                    'beginner': ['Python.org Tutorial', 'Codecademy Python', 'Python Crash Course book'],
                    'intermediate': ['Real Python', 'Python Tricks book', 'Flask/Django tutorials'],
                    'advanced': ['Effective Python book', 'Python internals', 'Open source contributions']
                },
                'javascript': {
                    'beginner': ['MDN JavaScript Guide', 'freeCodeCamp', 'JavaScript.info'],
                    'intermediate': ['You Don\'t Know JS books', 'ES6+ features', 'Node.js tutorials'],
                    'advanced': ['JavaScript patterns', 'V8 engine internals', 'Framework development']
                },
                'react': {
                    'beginner': ['React official tutorial', 'React for Beginners', 'Create React App'],
                    'intermediate': ['React Hooks', 'Context API', 'React Router'],
                    'advanced': ['React internals', 'Custom hooks', 'Performance optimization']
                },
                'aws': {
                    'beginner': ['AWS Free Tier', 'AWS Cloud Practitioner', 'AWS Fundamentals'],
                    'intermediate': ['Solutions Architect Associate', 'EC2, S3, RDS deep dive'],
                    'advanced': ['Solutions Architect Professional', 'DevOps Professional', 'Security Specialty']
                },
                'docker': {
                    'beginner': ['Docker official tutorial', 'Docker for Beginners', 'Containerization basics'],
                    'intermediate': ['Docker Compose', 'Multi-stage builds', 'Docker networking'],
                    'advanced': ['Docker internals', 'Custom images', 'Docker security']
                },
                'sql': {
                    'beginner': ['W3Schools SQL', 'SQLBolt', 'Basic queries and joins'],
                    'intermediate': ['Advanced queries', 'Stored procedures', 'Database design'],
                    'advanced': ['Query optimization', 'Database administration', 'NoSQL alternatives']
                }
            }
            
            # Define skill difficulty and learning time estimates (in weeks)
            self._skill_difficulty = {
                # Programming Languages
                'python': {'difficulty': 'medium', 'time_weeks': 8, 'prerequisites': []},
                'javascript': {'difficulty': 'medium', 'time_weeks': 6, 'prerequisites': ['html', 'css']},
                'java': {'difficulty': 'hard', 'time_weeks': 12, 'prerequisites': []},
                'c++': {'difficulty': 'hard', 'time_weeks': 16, 'prerequisites': ['c']},
                'sql': {'difficulty': 'easy', 'time_weeks': 4, 'prerequisites': []},
                
                # Web Technologies
                'react': {'difficulty': 'medium', 'time_weeks': 6, 'prerequisites': ['javascript', 'html', 'css']},
                'angular': {'difficulty': 'hard', 'time_weeks': 8, 'prerequisites': ['javascript', 'typescript']},
                'vue': {'difficulty': 'easy', 'time_weeks': 4, 'prerequisites': ['javascript', 'html', 'css']},
                'node.js': {'difficulty': 'medium', 'time_weeks': 5, 'prerequisites': ['javascript']},
                
                # Cloud & DevOps
                'aws': {'difficulty': 'hard', 'time_weeks': 12, 'prerequisites': ['linux', 'networking']},
                'docker': {'difficulty': 'medium', 'time_weeks': 4, 'prerequisites': ['linux']},
                'kubernetes': {'difficulty': 'hard', 'time_weeks': 8, 'prerequisites': ['docker', 'linux']},
                'terraform': {'difficulty': 'medium', 'time_weeks': 6, 'prerequisites': ['aws']},
                
                # Databases
                'mysql': {'difficulty': 'easy', 'time_weeks': 3, 'prerequisites': ['sql']},
                'postgresql': {'difficulty': 'medium', 'time_weeks': 4, 'prerequisites': ['sql']},
                'mongodb': {'difficulty': 'medium', 'time_weeks': 5, 'prerequisites': []},
                'redis': {'difficulty': 'easy', 'time_weeks': 2, 'prerequisites': []},
                
                # Fundamentals
                'html': {'difficulty': 'easy', 'time_weeks': 2, 'prerequisites': []},
                'css': {'difficulty': 'easy', 'time_weeks': 3, 'prerequisites': ['html']},
                'git': {'difficulty': 'easy', 'time_weeks': 2, 'prerequisites': []},
                'linux': {'difficulty': 'medium', 'time_weeks': 6, 'prerequisites': []}
            }
            
        except Exception as e:
            self.logger.error(f"Error initializing learning data: {str(e)}")
            self._learning_resources = {}
            self._skill_difficulty = {}
    
    def analyze_skill_gaps(self, user_skills: List[str], target_jobs: Optional[List[int]] = None, 
                          target_role: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive skill gap analysis
        
        Args:
            user_skills: List of user's current skills
            target_jobs: List of job IDs to analyze against (optional)
            target_role: Target career role for analysis (optional)
            
        Returns:
            Dictionary with gap analysis results and recommendations
        """
        try:
            analysis_results = {
                'user_skills': user_skills,
                'user_skills_count': len(user_skills),
                'target_jobs_analyzed': 0,
                'skill_gaps': [],
                'learning_path': [],
                'priority_skills': [],
                'estimated_learning_time': 0,
                'career_readiness': {}
            }
            
            # Analyze against specific jobs if provided
            if target_jobs:
                job_gaps = self._analyze_job_gaps(user_skills, target_jobs)
                analysis_results.update(job_gaps)
            
            # Analyze against career role if provided
            if target_role:
                career_gaps = self._analyze_career_gaps(user_skills, target_role)
                analysis_results['career_readiness'] = career_gaps
            
            # Get general market gap analysis
            market_gaps = self._analyze_market_gaps(user_skills)
            analysis_results['market_gaps'] = market_gaps
            
            # Generate learning path
            learning_path = self._generate_learning_path(analysis_results['skill_gaps'])
            analysis_results['learning_path'] = learning_path
            analysis_results['estimated_learning_time'] = sum(step['estimated_weeks'] for step in learning_path)
            
            # Identify priority skills
            priority_skills = self._identify_priority_skills(analysis_results['skill_gaps'])
            analysis_results['priority_skills'] = priority_skills
            
            return {
                'success': True,
                'analysis': analysis_results
            }
            
        except Exception as e:
            self.logger.error(f"Error in skill gap analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_job_gaps(self, user_skills: List[str], job_ids: List[int]) -> Dict[str, Any]:
        """Analyze skill gaps against specific job postings"""
        try:
            jobs = JobApplication.query.filter(JobApplication.id.in_(job_ids)).all()
            if not jobs:
                return {'target_jobs_analyzed': 0, 'skill_gaps': []}
            
            all_required_skills = []
            job_skill_analysis = []
            
            for job in jobs:
                if job.description:
                    # Extract skills from job description
                    extraction_result = self.extraction_service.extract_skills_enhanced(job.description)
                    if extraction_result['success']:
                        job_skills = extraction_result['skills']
                        all_required_skills.extend(job_skills)
                        
                        # Analyze match for this specific job
                        match_result = self.matching_service.match_skills_against_job(
                            user_skills, job.description
                        )
                        
                        job_skill_analysis.append({
                            'job_id': job.id,
                            'company': job.company,
                            'title': job.title,
                            'required_skills': job_skills,
                            'matched_skills': match_result.get('matched_skills', []),
                            'missing_skills': match_result.get('missing_skills', []),
                            'match_percentage': match_result.get('match_score', 0)
                        })
            
            # Find most common missing skills across all jobs
            skill_gaps = self._calculate_skill_gaps(user_skills, all_required_skills)
            
            return {
                'target_jobs_analyzed': len(jobs),
                'job_analyses': job_skill_analysis,
                'skill_gaps': skill_gaps,
                'average_match_score': sum(job['match_percentage'] for job in job_skill_analysis) / len(job_skill_analysis) if job_skill_analysis else 0
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing job gaps: {str(e)}")
            return {'target_jobs_analyzed': 0, 'skill_gaps': []}
    
    def _analyze_career_gaps(self, user_skills: List[str], target_role: str) -> Dict[str, Any]:
        """Analyze skill gaps for a specific career path"""
        try:
            career_analysis = self.recommendation_service.get_career_path_analysis(user_skills)
            
            if not career_analysis['success'] or target_role not in career_analysis['career_paths']:
                return {}
            
            role_data = career_analysis['career_paths'][target_role]
            
            return {
                'target_role': target_role,
                'readiness_score': role_data['readiness_score'],
                'core_skills_gap': role_data['core_skills'],
                'recommended_skills_gap': role_data['recommended_skills'],
                'advanced_skills_gap': role_data['advanced_skills'],
                'missing_core_skills': role_data['missing_core_skills'],
                'next_steps': self._get_career_next_steps(role_data)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing career gaps: {str(e)}")
            return {}
    
    def _analyze_market_gaps(self, user_skills: List[str]) -> Dict[str, Any]:
        """Analyze skill gaps based on market trends"""
        try:
            # Get skill recommendations based on market trends
            recommendations = self.recommendation_service.get_skill_recommendations(
                user_skills, limit=15
            )
            
            if not recommendations['success']:
                return {}
            
            # Categorize recommendations by source and priority
            market_gaps = {
                'trending_skills': [],
                'high_demand_skills': [],
                'complementary_skills': []
            }
            
            for rec in recommendations['recommendations']:
                if rec['source'] == 'market_trends':
                    market_gaps['trending_skills'].append(rec)
                elif rec['source'] == 'gap_analysis':
                    market_gaps['high_demand_skills'].append(rec)
                elif rec['source'] == 'complementary':
                    market_gaps['complementary_skills'].append(rec)
            
            return market_gaps
            
        except Exception as e:
            self.logger.error(f"Error analyzing market gaps: {str(e)}")
            return {}
    
    def _calculate_skill_gaps(self, user_skills: List[str], required_skills: List[str]) -> List[Dict[str, Any]]:
        """Calculate skill gaps with frequency and importance"""
        user_skills_lower = [skill.lower() for skill in user_skills]
        skill_counter = Counter(required_skills)
        
        gaps = []
        for skill, frequency in skill_counter.most_common():
            if skill.lower() not in user_skills_lower:
                gap_info = {
                    'skill': skill,
                    'frequency': frequency,
                    'importance': self._calculate_skill_importance(skill, frequency, len(required_skills)),
                    'difficulty': self._get_skill_difficulty(skill),
                    'estimated_learning_time': self._get_learning_time(skill),
                    'prerequisites': self._get_skill_prerequisites(skill)
                }
                gaps.append(gap_info)
        
        # Sort by importance score
        return sorted(gaps, key=lambda x: x['importance'], reverse=True)
    
    def _calculate_skill_importance(self, skill: str, frequency: int, total_skills: int) -> float:
        """Calculate importance score for a skill"""
        # Base importance on frequency
        frequency_score = (frequency / total_skills) * 100
        
        # Adjust based on skill type and market demand
        skill_lower = skill.lower()
        
        # High-value skills get bonus points
        high_value_skills = ['python', 'javascript', 'react', 'aws', 'docker', 'kubernetes', 'sql']
        if any(hvs in skill_lower for hvs in high_value_skills):
            frequency_score *= 1.5
        
        # Emerging technologies get bonus
        emerging_skills = ['machine learning', 'ai', 'blockchain', 'microservices', 'serverless']
        if any(es in skill_lower for es in emerging_skills):
            frequency_score *= 1.3
        
        return round(min(frequency_score, 100), 1)
    
    def _generate_learning_path(self, skill_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate an optimized learning path"""
        if not skill_gaps:
            return []
        
        # Sort skills by prerequisites and difficulty
        learning_path = []
        skills_to_learn = skill_gaps[:10]  # Focus on top 10 gaps
        
        # Group skills by prerequisites
        prerequisite_graph = {}
        for gap in skills_to_learn:
            skill = gap['skill'].lower()
            prerequisites = gap.get('prerequisites', [])
            prerequisite_graph[skill] = prerequisites
        
        # Topological sort to determine learning order
        ordered_skills = self._topological_sort(prerequisite_graph)
        
        # Create learning path with phases
        current_phase = 1
        phase_skills = []
        
        for skill in ordered_skills:
            # Find the original gap data
            gap_data = next((g for g in skills_to_learn if g['skill'].lower() == skill), None)
            if not gap_data:
                continue
            
            learning_step = {
                'phase': current_phase,
                'skill': gap_data['skill'],
                'difficulty': gap_data['difficulty'],
                'estimated_weeks': gap_data['estimated_learning_time'],
                'importance': gap_data['importance'],
                'prerequisites': gap_data['prerequisites'],
                'resources': self._get_learning_resources(skill),
                'milestones': self._get_skill_milestones(skill)
            }
            
            phase_skills.append(learning_step)
            
            # Start new phase every 3 skills or when difficulty changes significantly
            if len(phase_skills) >= 3:
                learning_path.extend(phase_skills)
                phase_skills = []
                current_phase += 1
        
        # Add remaining skills
        if phase_skills:
            learning_path.extend(phase_skills)
        
        return learning_path
    
    def _topological_sort(self, graph: Dict[str, List[str]]) -> List[str]:
        """Topological sort for prerequisite ordering"""
        visited = set()
        temp_visited = set()
        result = []
        
        def dfs(node):
            if node in temp_visited:
                return  # Cycle detected, skip
            if node in visited:
                return
            
            temp_visited.add(node)
            for prereq in graph.get(node, []):
                if prereq in graph:  # Only process if prereq is in our skill list
                    dfs(prereq)
            
            temp_visited.remove(node)
            visited.add(node)
            result.append(node)
        
        for node in graph:
            if node not in visited:
                dfs(node)
        
        return result
    
    def _identify_priority_skills(self, skill_gaps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify high-priority skills to learn first"""
        if not skill_gaps:
            return []
        
        priority_skills = []
        
        for gap in skill_gaps[:5]:  # Top 5 gaps
            priority_score = 0
            
            # High importance skills
            if gap['importance'] > 70:
                priority_score += 10
            
            # Easy to learn skills (quick wins)
            if gap['difficulty'] == 'easy':
                priority_score += 5
            
            # Skills with no prerequisites
            if not gap.get('prerequisites', []):
                priority_score += 3
            
            # High frequency skills
            if gap['frequency'] > 3:
                priority_score += 2
            
            priority_skills.append({
                **gap,
                'priority_score': priority_score,
                'priority_reason': self._get_priority_reason(gap, priority_score)
            })
        
        return sorted(priority_skills, key=lambda x: x['priority_score'], reverse=True)
    
    def _get_priority_reason(self, gap: Dict[str, Any], score: int) -> str:
        """Get human-readable reason for skill priority"""
        reasons = []
        
        if gap['importance'] > 70:
            reasons.append("high market demand")
        if gap['difficulty'] == 'easy':
            reasons.append("quick to learn")
        if not gap.get('prerequisites', []):
            reasons.append("no prerequisites")
        if gap['frequency'] > 3:
            reasons.append("frequently required")
        
        return ", ".join(reasons) if reasons else "recommended for career growth"
    
    def _get_skill_difficulty(self, skill: str) -> str:
        """Get difficulty level for a skill"""
        skill_lower = skill.lower()
        return self._skill_difficulty.get(skill_lower, {}).get('difficulty', 'medium')
    
    def _get_learning_time(self, skill: str) -> int:
        """Get estimated learning time in weeks"""
        skill_lower = skill.lower()
        return self._skill_difficulty.get(skill_lower, {}).get('time_weeks', 6)
    
    def _get_skill_prerequisites(self, skill: str) -> List[str]:
        """Get prerequisites for a skill"""
        skill_lower = skill.lower()
        return self._skill_difficulty.get(skill_lower, {}).get('prerequisites', [])
    
    def _get_learning_resources(self, skill: str) -> Dict[str, List[str]]:
        """Get learning resources for a skill"""
        skill_lower = skill.lower()
        return self._learning_resources.get(skill_lower, {
            'beginner': ['Online tutorials', 'Documentation'],
            'intermediate': ['Practice projects', 'Online courses'],
            'advanced': ['Advanced books', 'Open source contributions']
        })
    
    def _get_skill_milestones(self, skill: str) -> List[str]:
        """Get learning milestones for a skill"""
        skill_lower = skill.lower()
        
        # Default milestones
        milestones = [
            f"Complete basic {skill} tutorial",
            f"Build a simple project using {skill}",
            f"Understand {skill} best practices",
            f"Complete intermediate {skill} course",
            f"Build a complex project with {skill}"
        ]
        
        # Skill-specific milestones
        if skill_lower == 'python':
            milestones = [
                "Learn Python syntax and basic concepts",
                "Build a simple calculator or game",
                "Understand OOP in Python",
                "Learn a Python framework (Django/Flask)",
                "Build a web application"
            ]
        elif skill_lower == 'react':
            milestones = [
                "Understand React components and JSX",
                "Build a simple React app",
                "Learn React Hooks",
                "Implement state management",
                "Build a full-stack React application"
            ]
        elif skill_lower == 'aws':
            milestones = [
                "Complete AWS Cloud Practitioner",
                "Deploy a simple application on EC2",
                "Learn S3 and RDS",
                "Implement CI/CD pipeline",
                "Design scalable architecture"
            ]
        
        return milestones
    
    def _get_career_next_steps(self, role_data: Dict[str, Any]) -> List[str]:
        """Get next steps for career development"""
        next_steps = []
        
        # Focus on missing core skills first
        missing_core = role_data.get('missing_core_skills', [])
        if missing_core:
            next_steps.append(f"Learn core skills: {', '.join(missing_core[:3])}")
        
        # Then recommended skills
        rec_percentage = role_data.get('recommended_skills', {}).get('percentage', 0)
        if rec_percentage < 50:
            next_steps.append("Focus on recommended skills to improve job readiness")
        
        # Finally advanced skills
        if rec_percentage > 70:
            next_steps.append("Consider learning advanced skills for senior roles")
        
        return next_steps

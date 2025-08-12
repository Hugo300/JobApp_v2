"""
Centralized skill constants and data structures

This module consolidates skill-related constants, dictionaries, and patterns
that are used across multiple services to reduce duplication.
"""

# Skill relationship mappings (used by recommendation service)
SKILL_RELATIONSHIPS = {
    'python': ['django', 'flask', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
    'javascript': ['react', 'node.js', 'express', 'vue', 'angular', 'typescript'],
    'java': ['spring', 'spring boot', 'maven', 'gradle', 'hibernate'],
    'react': ['javascript', 'typescript', 'redux', 'next.js', 'html', 'css'],
    'aws': ['docker', 'kubernetes', 'terraform', 'jenkins', 'linux'],
    'docker': ['kubernetes', 'aws', 'jenkins', 'terraform', 'linux'],
    'sql': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch'],
    'machine learning': ['python', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch'],
    'data science': ['python', 'r', 'sql', 'pandas', 'numpy', 'matplotlib', 'jupyter'],
    'devops': ['docker', 'kubernetes', 'aws', 'jenkins', 'terraform', 'ansible', 'git']
}

# Programming languages with variations (used by enhanced extraction)
PROGRAMMING_LANGUAGES = {
    'python': ['python', 'py', 'python3', 'python2', 'cpython', 'pypy'],
    'javascript': ['javascript', 'js', 'ecmascript', 'es6', 'es2015', 'es2020'],
    'typescript': ['typescript', 'ts'],
    'java': ['java', 'openjdk', 'oracle java'],
    'c#': ['c#', 'csharp', 'c sharp', '.net', 'dotnet'],
    'c++': ['c++', 'cpp', 'c plus plus', 'cplusplus'],
    'c': ['c programming', 'ansi c'],
    'php': ['php', 'php7', 'php8'],
    'ruby': ['ruby', 'ruby on rails', 'ror'],
    'go': ['go', 'golang', 'go lang'],
    'rust': ['rust', 'rust lang'],
    'swift': ['swift', 'swift ui', 'swiftui'],
    'kotlin': ['kotlin', 'kotlin/jvm'],
    'scala': ['scala', 'scala.js'],
    'r': ['r programming', 'r language', 'r statistical'],
    'matlab': ['matlab', 'octave'],
    'sql': ['sql', 'structured query language', 'mysql', 'postgresql', 'sqlite', 'mssql', 'oracle sql']
}

# Web technologies and frameworks
WEB_TECHNOLOGIES = {
    'react': ['react', 'reactjs', 'react.js', 'react native', 'next.js', 'nextjs'],
    'angular': ['angular', 'angularjs', 'angular2', 'angular4', 'angular8', 'angular12'],
    'vue': ['vue', 'vuejs', 'vue.js', 'vue3', 'nuxt', 'nuxtjs'],
    'node.js': ['node', 'nodejs', 'node.js', 'express', 'expressjs'],
    'django': ['django', 'django rest framework', 'drf'],
    'flask': ['flask', 'flask-restful'],
    'spring': ['spring', 'spring boot', 'spring framework', 'spring mvc'],
    'laravel': ['laravel', 'eloquent'],
    'rails': ['rails', 'ruby on rails', 'ror'],
    'asp.net': ['asp.net', 'asp.net core', 'asp.net mvc'],
    'html': ['html', 'html5', 'xhtml'],
    'css': ['css', 'css3', 'sass', 'scss', 'less', 'stylus'],
    'bootstrap': ['bootstrap', 'bootstrap4', 'bootstrap5'],
    'tailwind': ['tailwind', 'tailwindcss', 'tailwind css']
}

# Cloud and DevOps technologies
CLOUD_DEVOPS = {
    'aws': ['aws', 'amazon web services', 'ec2', 's3', 'lambda', 'cloudformation', 'eks', 'rds'],
    'azure': ['azure', 'microsoft azure', 'azure devops', 'azure functions'],
    'gcp': ['gcp', 'google cloud', 'google cloud platform', 'gke', 'bigquery'],
    'docker': ['docker', 'containerization', 'dockerfile'],
    'kubernetes': ['kubernetes', 'k8s', 'kubectl', 'helm'],
    'jenkins': ['jenkins', 'jenkins pipeline'],
    'terraform': ['terraform', 'infrastructure as code', 'iac'],
    'ansible': ['ansible', 'ansible playbook'],
    'git': ['git', 'github', 'gitlab', 'bitbucket', 'version control']
}

# Database technologies
DATABASES = {
    'mysql': ['mysql', 'mariadb'],
    'postgresql': ['postgresql', 'postgres', 'psql'],
    'mongodb': ['mongodb', 'mongo', 'mongoose'],
    'redis': ['redis', 'redis cache'],
    'elasticsearch': ['elasticsearch', 'elastic search', 'elk stack'],
    'cassandra': ['cassandra', 'apache cassandra'],
    'oracle': ['oracle', 'oracle database', 'plsql'],
    'sql server': ['sql server', 'mssql', 'microsoft sql server'],
    'sqlite': ['sqlite', 'sqlite3'],
    'dynamodb': ['dynamodb', 'amazon dynamodb']
}

# Combined skill dictionary for easy access
ALL_SKILL_VARIATIONS = {
    **PROGRAMMING_LANGUAGES,
    **WEB_TECHNOLOGIES,
    **CLOUD_DEVOPS,
    **DATABASES
}

# Regex patterns for skill extraction
PROGRAMMING_PATTERNS = [
    r'\b(?:python|py|javascript|js|java|c#|c\+\+|php|ruby|go|rust|swift|kotlin)\b',
    r'\b(?:typescript|ts|scala|matlab|sql)\b',
    r'\b(?:node\.?js|react\.?js|vue\.?js|angular\.?js)\b'
]

FRAMEWORK_PATTERNS = [
    r'\b(?:django|flask|spring|laravel|rails|express)\b',
    r'\b(?:react|angular|vue|bootstrap|tailwind)\b',
    r'\b(?:asp\.net|\.net|spring boot)\b'
]

VERSION_PATTERNS = [
    r'\b(?:python|java|node|php|ruby)\s+\d+(?:\.\d+)?\b',
    r'\b(?:angular|react|vue)\s+\d+(?:\.\d+)?\b'
]

# Career path definitions
CAREER_PATHS = {
    'Full Stack Developer': {
        'core_skills': ['javascript', 'html', 'css', 'react', 'node.js', 'sql'],
        'recommended_skills': ['typescript', 'mongodb', 'aws', 'docker', 'git'],
        'advanced_skills': ['kubernetes', 'microservices', 'graphql', 'redis']
    },
    'Data Scientist': {
        'core_skills': ['python', 'sql', 'pandas', 'numpy', 'matplotlib'],
        'recommended_skills': ['scikit-learn', 'tensorflow', 'jupyter', 'r', 'statistics'],
        'advanced_skills': ['pytorch', 'deep learning', 'mlops', 'spark', 'hadoop']
    },
    'DevOps Engineer': {
        'core_skills': ['linux', 'docker', 'kubernetes', 'aws', 'git'],
        'recommended_skills': ['terraform', 'ansible', 'jenkins', 'monitoring', 'scripting'],
        'advanced_skills': ['service mesh', 'gitops', 'chaos engineering', 'security']
    },
    'Backend Developer': {
        'core_skills': ['python', 'java', 'sql', 'api design', 'git'],
        'recommended_skills': ['docker', 'redis', 'mongodb', 'microservices', 'testing'],
        'advanced_skills': ['kubernetes', 'event sourcing', 'cqrs', 'distributed systems']
    },
    'Frontend Developer': {
        'core_skills': ['javascript', 'html', 'css', 'react', 'responsive design'],
        'recommended_skills': ['typescript', 'sass', 'webpack', 'testing', 'accessibility'],
        'advanced_skills': ['performance optimization', 'pwa', 'web components', 'webgl']
    },
    'Mobile Developer': {
        'core_skills': ['swift', 'kotlin', 'react native', 'mobile ui/ux'],
        'recommended_skills': ['firebase', 'core data', 'rest api', 'git'],
        'advanced_skills': ['ar/vr', 'machine learning on mobile', 'cross-platform']
    }
}

# Skill difficulty and learning time estimates
SKILL_DIFFICULTY = {
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

# Learning resources by skill and level
LEARNING_RESOURCES = {
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

# Skill categorization mappings
SKILL_CATEGORIES = {
    'Programming Languages': ['python', 'javascript', 'java', 'c#', 'c++', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin'],
    'Web Technologies': ['react', 'angular', 'vue', 'html', 'css', 'node.js', 'express', 'django', 'flask'],
    'Cloud & DevOps': ['aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'jenkins', 'ansible'],
    'Databases': ['mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'sql', 'oracle'],
    'Data Science & AI': ['pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch', 'jupyter', 'matplotlib'],
    'Mobile Development': ['swift', 'kotlin', 'react native', 'flutter', 'xamarin'],
    'Design & UX': ['figma', 'sketch', 'adobe xd', 'photoshop', 'illustrator', 'ui/ux'],
    'Project Management': ['agile', 'scrum', 'kanban', 'jira', 'confluence', 'project management']
}

# Soft skills keywords for classification
SOFT_SKILLS_KEYWORDS = [
    'communication', 'leadership', 'teamwork', 'problem solving',
    'analytical', 'creative', 'adaptable', 'organized', 'detail oriented',
    'time management', 'critical thinking', 'collaboration', 'presentation',
    'negotiation', 'mentoring', 'coaching', 'strategic thinking'
]

# Noise patterns to filter out during extraction
NOISE_PATTERNS = [
    # Generic phrases
    'related industry', 'relevant experience', 'similar role', 'comparable position',
    'equivalent experience', 'related field', 'similar background', 'relevant background',
    'industry experience', 'professional experience', 'work experience', 'prior experience',
    
    # Time-related phrases
    'years experience', 'years of experience', 'year experience', 'months experience',
    'minimum years', 'plus years', 'or more years', 'at least years',
    
    # Generic requirements
    'strong background', 'solid background', 'proven track record', 'demonstrated ability',
    'ability to work', 'willingness to', 'desire to', 'passion for', 'interest in',
    
    # Location/logistics
    'remote work', 'on site', 'hybrid work', 'flexible schedule', 'full time', 'part time',
    'contract position', 'permanent position', 'temporary position'
]

def get_skill_category(skill: str) -> str:
    """Get the category for a given skill"""
    skill_lower = skill.lower()
    
    for category, skills in SKILL_CATEGORIES.items():
        if any(s in skill_lower for s in skills):
            return category
    
    return 'Other Technical'

def get_canonical_skill_name(skill: str) -> str:
    """Get the canonical name for a skill variation"""
    skill_lower = skill.lower()
    
    for canonical, variations in ALL_SKILL_VARIATIONS.items():
        if skill_lower in [v.lower() for v in variations]:
            return canonical
    
    return skill_lower

def is_soft_skill(skill: str) -> bool:
    """Check if a skill is a soft skill"""
    skill_lower = skill.lower()
    return any(keyword in skill_lower for keyword in SOFT_SKILLS_KEYWORDS)

def is_noise_skill(skill: str) -> bool:
    """Check if a skill is likely noise"""
    skill_lower = skill.lower().strip()
    return any(pattern in skill_lower for pattern in NOISE_PATTERNS)

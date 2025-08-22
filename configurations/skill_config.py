class SkillExtractionConfig:
    """Configuration for skill extraction and processing"""
    
    SPACY_MODEL = "en_core_web_lg"
    MIN_SKILL_LENGTH = 2
    
    # Noise patterns for filtering out non-skills
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
        'contract position', 'permanent position', 'temporary position',
        
        # Education levels (too generic)
        'bachelor degree', 'master degree', 'phd', 'high school', 'college degree',
        'university degree', 'advanced degree',
        
        # Company-specific
        'company culture', 'team environment', 'fast paced', 'startup environment',
        'corporate environment', 'small team', 'large team',
        
        # Vague descriptors
        'good understanding', 'basic knowledge', 'working knowledge', 'familiarity with',
        'exposure to', 'some experience', 'hands on experience'
    ]
    
    COMMON_WORDS = {'the', 'and', 'or', 'of', 'in', 'to', 'for', 'with', 'on', 'at', 'by', 'from'}
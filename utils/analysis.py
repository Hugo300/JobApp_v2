import re
from collections import Counter

def analyze_job_match(job_description, skills_list):
    """
    Analyze job description against user skills.
    Returns (match_score, matched_keywords, unmatched_keywords)
    """
    if not skills_list or not job_description:
        return 0, [], []
    
    # Convert everything to lowercase for comparison
    job_desc_lower = job_description.lower()
    skills_lower = [skill.lower().strip() for skill in skills_list]
    
    # Find matched and unmatched keywords
    matched_keywords = []
    unmatched_keywords = []
    
    for skill in skills_lower:
        # Check if skill appears in job description
        if skill in job_desc_lower:
            matched_keywords.append(skill)
        else:
            unmatched_keywords.append(skill)
    
    # Calculate match score
    if skills_list:
        match_score = (len(matched_keywords) / len(skills_list)) * 100
    else:
        match_score = 0
    
    return round(match_score, 1), matched_keywords, unmatched_keywords

def extract_keywords_from_description(job_description):
    """
    Extract potential keywords from job description.
    This is a simple implementation - could be enhanced with NLP libraries.
    """
    if not job_description:
        return []
    
    # Convert to lowercase
    text = job_description.lower()
    
    # Remove common words and punctuation
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her', 'its', 'our', 'their',
        'mine', 'yours', 'hers', 'ours', 'theirs', 'am', 'is', 'are', 'was', 'were',
        'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'can', 'shall', 'should', 'would', 'could'
    }
    
    # Extract words (alphanumeric characters only)
    words = re.findall(r'\b[a-zA-Z]+\b', text)
    
    # Filter out stop words and short words
    keywords = [word for word in words if word not in stop_words and len(word) > 2]
    
    # Count frequency and return most common
    word_counts = Counter(keywords)
    return [word for word, count in word_counts.most_common(20)]

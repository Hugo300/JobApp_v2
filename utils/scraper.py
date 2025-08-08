import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time

def scrape_job_details(url):
    """
    Scrape job details from a given URL.
    Returns (title, company, description) tuple.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Try to extract title
        title = None
        title_selectors = [
            'h1',
            '.job-title',
            '.title',
            '[data-testid="job-title"]',
            '.job-header h1',
            '.job-details h1'
        ]
        
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
        
        # Try to extract company name
        company = None
        company_selectors = [
            '.company-name',
            '.employer',
            '.organization',
            '[data-testid="company-name"]',
            '.job-header .company',
            '.job-details .company'
        ]
        
        for selector in company_selectors:
            company_elem = soup.select_one(selector)
            if company_elem:
                company = company_elem.get_text().strip()
                break
        
        # If company not found, try to extract from URL
        if not company:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            if domain:
                company = domain.replace('www.', '').split('.')[0].title()
        
        # Try to extract description
        description = None
        description_selectors = [
            '.job-description',
            '.description',
            '.job-details',
            '[data-testid="job-description"]',
            '.job-content',
            '.job-body'
        ]
        
        for selector in description_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text().strip()
                break
        
        # If no specific description found, try to get all text content
        if not description:
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            description = ' '.join(chunk for chunk in chunks if chunk)
            
            # Limit description length
            if len(description) > 2000:
                description = description[:2000] + "..."
        
        return title, company, description
        
    except requests.RequestException as e:
        raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error scraping job details: {str(e)}")

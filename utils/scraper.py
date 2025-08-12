import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse
import time
import json

# Optional selenium imports for advanced scraping
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

def get_site_specific_headers(url):
    """Get headers optimized for specific job sites"""
    domain = urlparse(url).netloc.lower()

    base_headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

    if 'linkedin.com' in domain:
        base_headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
    elif 'indeed.com' in domain:
        base_headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
    elif 'glassdoor.com' in domain:
        base_headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })
    else:
        base_headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    return base_headers

def scrape_linkedin_job(soup, url):
    """Specific scraper for LinkedIn job posts"""
    title = None
    company = None
    description = None

    # LinkedIn title selectors
    title_selectors = [
        'h1.top-card-layout__title',
        'h1[data-test-id="job-title"]',
        '.job-details-jobs-unified-top-card__job-title h1',
        '.jobs-unified-top-card__job-title h1',
        'h1.t-24'
    ]

    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get_text().strip()
            break

    # LinkedIn company selectors
    company_selectors = [
        '.job-details-jobs-unified-top-card__company-name a',
        '.jobs-unified-top-card__company-name a',
        '.job-details-jobs-unified-top-card__company-name',
        '.jobs-unified-top-card__company-name',
        'a[data-test-id="job-poster-name"]'
    ]

    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            company = elem.get_text().strip()
            break

    # LinkedIn description selectors
    description_selectors = [
        '.job-details-jobs-unified-top-card__job-description',
        '.jobs-description__content',
        '.jobs-box__html-content',
        '.job-details-module',
        '[data-test-id="job-description"]'
    ]

    for selector in description_selectors:
        elem = soup.select_one(selector)
        if elem:
            description = elem.get_text().strip()
            break

    return title, company, description

def scrape_indeed_job(soup, url):
    """Specific scraper for Indeed job posts"""
    title = None
    company = None
    description = None

    # Indeed title selectors
    title_selectors = [
        'h1[data-testid="jobsearch-JobInfoHeader-title"]',
        'h1.jobsearch-JobInfoHeader-title',
        '.jobsearch-JobInfoHeader-title span',
        'h1.it-jd-title'
    ]

    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get_text().strip()
            break

    # Indeed company selectors
    company_selectors = [
        '[data-testid="inlineHeader-companyName"] a',
        '[data-testid="inlineHeader-companyName"]',
        '.jobsearch-InlineCompanyRating a',
        '.jobsearch-CompanyInfoContainer a'
    ]

    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            company = elem.get_text().strip()
            break

    # Indeed description selectors
    description_selectors = [
        '#jobDescriptionText',
        '.jobsearch-jobDescriptionText',
        '[data-testid="job-description"]',
        '.jobsearch-JobComponent-description'
    ]

    for selector in description_selectors:
        elem = soup.select_one(selector)
        if elem:
            description = elem.get_text().strip()
            break

    return title, company, description

def scrape_generic_job(soup, url):
    """Generic scraper for job sites not specifically supported"""
    title = None
    company = None
    description = None

    # Generic title selectors
    title_selectors = [
        'h1',
        '.job-title',
        '.title',
        '[data-testid="job-title"]',
        '.job-header h1',
        '.job-details h1',
        '.position-title',
        '.job-name'
    ]

    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get_text().strip()
            break

    # Generic company selectors
    company_selectors = [
        '.company-name',
        '.employer',
        '.organization',
        '[data-testid="company-name"]',
        '.job-header .company',
        '.job-details .company',
        '.employer-name',
        '.company'
    ]

    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            company = elem.get_text().strip()
            break

    # If company not found, try to extract from URL
    if not company:
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        if domain:
            company = domain.replace('www.', '').split('.')[0].title()

    # Generic description selectors
    description_selectors = [
        '.job-description',
        '.description',
        '.job-details',
        '[data-testid="job-description"]',
        '.job-content',
        '.job-body',
        '.job-summary',
        '.position-description'
    ]

    for selector in description_selectors:
        elem = soup.select_one(selector)
        if elem:
            description = elem.get_text().strip()
            break

    # If no specific description found, try to get all text content
    if not description:
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "header", "footer"]):
            script.decompose()

        # Get text content
        text = soup.get_text()
        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        description = ' '.join(chunk for chunk in chunks if chunk)

    return title, company, description

def clean_text(text):
    """Clean and normalize extracted text"""
    if not text:
        return None

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    # Remove common unwanted patterns
    text = re.sub(r'^\s*[-•]\s*', '', text)  # Remove leading bullets
    text = re.sub(r'\s*\|\s*', ' | ', text)  # Normalize separators

    # Remove very long sequences of the same character
    text = re.sub(r'(.)\1{10,}', r'\1\1\1', text)

    return text

def scrape_job_details(url):
    """
    Scrape job details from a given URL with site-specific optimizations.
    Returns (title, company, description) tuple.
    """
    headers = get_site_specific_headers(url)
    domain = urlparse(url).netloc.lower()

    try:
        # Add delay to avoid rate limiting
        time.sleep(1)

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff

        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')

        # Try site-specific scrapers first
        title, company, description = None, None, None

        if 'linkedin.com' in domain:
            title, company, description = scrape_linkedin_job(soup, url)
        elif 'indeed.com' in domain:
            title, company, description = scrape_indeed_job(soup, url)
        elif 'glassdoor.com' in domain:
            title, company, description = scrape_glassdoor_job(soup, url)

        # Fallback to generic scraping if site-specific failed
        if not title or not company or not description:
            generic_title, generic_company, generic_description = scrape_generic_job(soup, url)
            title = title or generic_title
            company = company or generic_company
            description = description or generic_description

        # Clean up extracted data
        if title:
            title = clean_text(title)
        if company:
            company = clean_text(company)
        if description:
            description = clean_text(description)
            # Limit description length
            if len(description) > 3000:
                description = description[:3000] + "..."

        return title, company, description

    except requests.RequestException as e:
        if "403" in str(e) or "Forbidden" in str(e):
            raise Exception(f"Access denied - the website may be blocking automated requests. Try copying the job details manually.")
        elif "404" in str(e):
            raise Exception(f"Job posting not found - the URL may be expired or incorrect.")
        elif "timeout" in str(e).lower():
            raise Exception(f"Request timed out - the website may be slow or unavailable.")
        else:
            raise Exception(f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise Exception(f"Error scraping job details: {str(e)}")

def scrape_glassdoor_job(soup, url):
    """Specific scraper for Glassdoor job posts"""
    title = None
    company = None
    description = None

    # Glassdoor title selectors
    title_selectors = [
        '[data-test="job-title"]',
        '.jobTitle',
        'h1[data-test="job-title"]',
        '.job-title'
    ]

    for selector in title_selectors:
        elem = soup.select_one(selector)
        if elem:
            title = elem.get_text().strip()
            break

    # Glassdoor company selectors
    company_selectors = [
        '[data-test="employer-name"]',
        '.employerName',
        'a[data-test="employer-name"]',
        '.employer-name'
    ]

    for selector in company_selectors:
        elem = soup.select_one(selector)
        if elem:
            company = elem.get_text().strip()
            break

    # Glassdoor description selectors
    description_selectors = [
        '[data-test="job-description"]',
        '.jobDescription',
        '.job-description-content',
        '.desc'
    ]

    for selector in description_selectors:
        elem = soup.select_one(selector)
        if elem:
            description = elem.get_text().strip()
            break

    return title, company, description

import os
import requests
from bs4 import BeautifulSoup
import re
import html2text 
from urllib.parse import urlparse
import time

from flask import current_app

# Optional selenium imports for advanced scraping
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    from webdriver_manager.chrome import ChromeDriverManager
    from webdriver_manager.core.os_manager import ChromeType
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False


def brave_options():
    brave_options = Options()
    brave_options.add_argument("--headless")  # Run in headless mode
    brave_options.add_argument("--disable-gpu")
    brave_options.add_argument("--no-sandbox")  # Required for running in certain environments
    brave_options.add_argument("--disable-dev-shm-usage")
    # We use a user-agent to mimic a real browser and avoid easy detection.
    brave_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    brave_options.binary_location = os.environ.get('BRAVE_BIN') or "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"

    return brave_options

def scrape_linkedin_job(page_html):
    """Specific scraper for LinkedIn job posts"""

    # Parse the content with BeautifulSoup
    soup = BeautifulSoup(page_html, 'html.parser')

    parsed_data = {}

    # Extract the job title using its CSS selector.
    title_elem = soup.select_one(".top-card-layout__title")
    parsed_data['title'] = title_elem.get_text(strip=True) if title_elem else "Title Not Found"

    # Extract the company name.
    topcard_elems = soup.select(".topcard__flavor")
    parsed_data['company'] = topcard_elems[0].get_text(strip=True) if topcard_elems else "Company Not Found"

    # Extract the job location.
    # Using soup.select to find all elements with the class "topcard__flavor"
    # The location is typically the second element in the list.
    location = topcard_elems[1].get_text(strip=True) if len(topcard_elems) > 1 else "Location Not Found"
    location_list = location.split(', ')

    parsed_data['office_location'] = location_list[0]
    parsed_data['country'] = location_list[1] if len(location_list) > 1 else ''

    # Description criteria, extracting info like seniority, contract type, etc.
    description_criteria_elems = soup.select(".description__job-criteria-item")

    for elem in description_criteria_elems:
        key = elem.select_one(".description__job-criteria-subheader").get_text(strip=True).lower().strip().replace(' ', '_')
        value= elem.select_one(".description__job-criteria-text").get_text(strip=True)
        parsed_data[key] = value


    # Your selected code for the job description goes here
    description_elem = soup.select_one(".description__text.description__text--rich")
    if description_elem:
        description_markdown = convert_html_to_markdown(str(description_elem))

        # Clean up markdown
        parsed_data['description'] = _clean_and_enhance_markdown(description_markdown)

        print("Extracted Job Description:")
    else:
        parsed_data['description'] = ''
        print("Job description element not found.")

    return parsed_data


def scrape_job_data(url: str) -> dict[str, str]:
    """
    Scrape job details from a given URL with site-specific optimizations.
    Returns (title, company, description) tuple.
    """
    domain = urlparse(url).netloc.lower()

    if domain == 'www.linkedin.com':
        if 'jobs/collections' in url: # convert the collections job page for the view page allowing sellenium to actually get information 
            job_id = url.split('=')[-1]
            url = f'https://{domain}/jobs/view/{job_id}'
        if 'jobs/search' in url:
            match = re.search(r'\?(currentJobId)\=(.*?)\&', url)
            
            if match:
                job_id = match.group(0).split('=')[1].replace('&', '').strip()
                url = f'https://{domain}/jobs/view/{job_id}'
            else:
                raise ValueError('Could not find job id in "job/search" url')

    try:
        # Add delay to avoid rate limiting
        time.sleep(1)

        # Make request with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Initialize the WebDriver. The ChromeDriverManager will download the correct
                # ChromeDriver for Brave based on its version.
                service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
                # Instantiate a Chrome driver, but with Brave-specific options
                driver = webdriver.Chrome(service=service, options=brave_options())
                
                # Navigate to the URL
                driver.get(url)

                if "expired_jd_redirect" in driver.current_url:
                    current_app.logger.warning("The job posting has expired or been redirected.")
                    raise Exception("Job no longer available")

                # Wait for the main content to load. This is crucial for dynamic websites.
                # We wait for the job title element to be present on the page.
                WebDriverWait(driver, 20).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, ".top-card-layout__title"))
                )

                # Get the full page source after all JavaScript has been executed.
                page_source = driver.page_source
                break
            except requests.RequestException as e:
                if attempt == max_retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff

        # Try site-specific scrapers first
        job_data = {}

        if 'linkedin.com' in domain:
            job_data = scrape_linkedin_job(page_source)

        return job_data

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

def convert_html_to_markdown(html_content):
    """
    Converts a string of HTML content into Markdown format.
    
    Args:
        html_content (str): The HTML string to be converted.

    Returns:
        str: The converted Markdown string.
    """
    # Pre-process HTML to improve structure
    #soup = BeautifulSoup(html_content, 'html.parser')
    
    # Convert common HTML structures to more markdown-friendly versions
    #preprocess_html_structure(soup)

    # Create an html2text converter instance.
    # We can customize it to ignore images, or specific tags if needed.
    converter = html2text.HTML2Text()
    converter.ignore_links = False          # Keep links
    converter.ignore_images = True          # Skip images
    converter.ignore_emphasis = False       # Keep bold/italic
    converter.body_width = 0               # No line wrapping
    converter.wrap_links = False           # Don't wrap long links
    converter.wrap_list_items = False      # Don't wrap list items
    converter.unicode_snob = True          # Use unicode characters
    converter.escape_snob = True           # Escape special characters properly
    converter.mark_code = True             # Mark code blocks
    converter.default_image_alt = ""       # Empty alt text for images
    converter.pad_tables = True            # Better table formatting
    
    # Convert the HTML to Markdown
    markdown_text = converter.handle(html_content)
    return markdown_text

def preprocess_html_structure(soup):
    """
    Pre-process HTML to improve markdown conversion by normalizing common patterns.
    """
    # Convert div elements that act as headers to proper header tags
    for div in soup.find_all('div'):
        if div.get_text(strip=True):
            # Check if this div looks like a header (short text, bold, etc.)
            text = div.get_text(strip=True)
            if (len(text) < 100 and 
                (div.find('strong') or div.find('b') or 
                 'font-weight:bold' in str(div.get('style', '')) or
                 'font-weight: bold' in str(div.get('style', '')))):
                # Convert to h3 if it looks like a section header
                div.name = 'h3'
    
    # Improve list detection - convert divs with bullet-like content to lists
    potential_lists = []
    for div in soup.find_all('div'):
        text = div.get_text(strip=True)
        if text and re.match(r'^[•·▪▫‣⁃]\s+|^[\-\*\+]\s+|^\d+[\.\)]\s+', text):
            potential_lists.append(div)
    
    # Group consecutive list items
    if potential_lists:
        current_list = []
        for div in potential_lists:
            if (not current_list or 
                (current_list and 
                 div.previous_sibling and 
                 current_list[-1] == div.previous_sibling)):
                current_list.append(div)
            else:
                if current_list:
                    create_proper_list(current_list)
                current_list = [div]
        
        if current_list:
            create_proper_list(current_list)

    # Convert spans with specific styling to proper emphasis
    for span in soup.find_all('span'):
        style = span.get('style', '').lower()
        if 'font-weight:bold' in style or 'font-weight: bold' in style:
            span.name = 'strong'
        elif 'font-style:italic' in style or 'font-style: italic' in style:
            span.name = 'em'

def create_proper_list(list_items):
    """Convert a group of div elements into a proper HTML list."""
    if not list_items:
        return
    
    # Determine if it's ordered or unordered
    first_text = list_items[0].get_text(strip=True)
    is_ordered = bool(re.match(r'^\d+[\.\)]\s+', first_text))
    
    # Create the list container
    list_tag = 'ol' if is_ordered else 'ul'
    list_elem = list_items[0].parent.new_tag(list_tag)
    
    # Convert each div to a list item
    for div in list_items:
        li = div.parent.new_tag('li')
        text = div.get_text(strip=True)
        # Remove bullet points or numbers
        clean_text = re.sub(r'^[•·▪▫‣⁃\-\*\+]\s+|^\d+[\.\)]\s+', '', text)
        li.string = clean_text
        list_elem.append(li)
    
    # Replace the first div with the list, remove others
    list_items[0].replace_with(list_elem)
    for div in list_items[1:]:
        div.decompose()

def _clean_and_enhance_markdown(text: str) -> str:
    """
    Enhanced markdown cleaning with better structure and formatting preservation.
    """
    if not text:
        return text
    
    # Fix encoding issues first
    text = _fix_encoding_issues(text)

    text = text.removesuffix('Show more Show less')
    text = text.removesuffix('show more show less')
    
    text = _normalize_whitespace(text)
    text = _enhance_headers(text)
    text = _enhance_lists(text)
    text = _clean_links_and_formatting(text)
    text = _final_cleanup(text)
    
    return text.strip()

def _fix_encoding_issues(text: str) -> str:
    """Fix common encoding issues in scraped text."""
    encoding_fixes = {
        'Ã¢â‚¬â„¢': "'",     # Smart apostrophe
        'Ã¢â‚¬Å"': '"',      # Smart quote open
        'Ã¢â‚¬': '"',        # Smart quote close  
        'Ã¢â‚¬"': '—',       # Em dash
        'Ã¢â‚¬"': '–',       # En dash
        'Ã¢â‚¬Â¦': '...',    # Ellipsis
        'Ã¢â‚¬Â¢': '•',      # Bullet point
        'â€™': "'",          # Another apostrophe variant
        'â€œ': '"',          # Left double quote
        'â€': '"',           # Right double quote
        'â€"': '—',          # Em dash variant
        'â€"': '–',          # En dash variant
        '&nbsp;': ' ',       # Non-breaking space
        '&amp;': '&',        # Ampersand
        '&lt;': '<',         # Less than
        '&gt;': '>',         # Greater than
        '&quot;': '"',       # Quote
        '&#39;': "'",        # Apostrophe
    }
    
    for bad, good in encoding_fixes.items():
        text = text.replace(bad, good)
    
    return text

def _normalize_whitespace(text: str) -> str:
    """Normalize whitespace while preserving intentional formatting."""
    # Remove excessive whitespace but preserve intentional line breaks
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Clean up spaces within lines
        cleaned_line = re.sub(r'[ \t]+', ' ', line.strip())
        cleaned_lines.append(cleaned_line)
    
    # Join lines back together
    text = '\n'.join(cleaned_lines)
    
    # Reduce multiple consecutive empty lines to at most 2
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def _fix_broken_bold_headers(text: str) -> str:
    """Fix broken bold headers that span multiple lines."""
    # Pattern 1: **Header\n\n** or **Header\n**
    # This handles cases where the closing ** is on its own line
    text = re.sub(r'\*\*([^\*\n]+)\n\n\s*\*\*', r'**\1**\n\n', text)
    text = re.sub(r'\*\*([^\*\n]+)\n\s*\*\*', r'**\1**\n', text)
    
    # Pattern 2: **Header\n\n** Start of text block
    # This handles cases where there's content after the broken bold
    text = re.sub(r'\*\*([^\*\n]+)\n\n\s*\*\*\s+([^\n]+)', r'**\1**\n\n\2', text)
    text = re.sub(r'\*\*([^\*\n]+)\n\s*\*\*\s+([^\n]+)', r'**\1**\n\n\2', text)
    
    # Pattern 3: Handle incomplete bold markers (just ** on a line)
    # Remove standalone ** markers that don't have matching content
    text = re.sub(r'\n\s*\*\*\s*\n', r'\n\n', text)
    
    return text

def fix_broken_formatting(text: str) -> str:
    """Fix various broken formatting patterns."""
    # Fix broken bold that spans across line breaks
    # **Text\n\nmore text** -> **Text**\n\nmore text
    text = re.sub(r'\*\*([^\*]+?)\n\n([^\*]+?)\*\*', r'**\1**\n\n\2', text)
    
    # Fix bold markers that are separated by whitespace
    # ** Text ** -> **Text**
    text = re.sub(r'\*\*\s+([^*]+?)\s+\*\*', r'**\1**', text)
    
    # Fix cases where bold marker is at start of line but content continues on next line
    # **Requirements\nSome content -> **Requirements**\nSome content
    text = re.sub(r'^\*\*([^*\n]+)\n([^*\n][^\n]*)', r'**\1**\n\n\2', text, flags=re.MULTILINE)
    
    # Remove empty bold markers
    text = re.sub(r'\*\*\s*\*\*', '', text)
    
    # Fix italic formatting similarly
    text = re.sub(r'\*\s+([^*]+?)\s+\*', r'*\1*', text)
    
    return text

def _enhance_headers(text: str) -> str:
    """Improve header detection and formatting."""
    text = _fix_broken_bold_headers(text)

    lines = text.split('\n')
    enhanced_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        if not stripped:
            enhanced_lines.append(line)
            continue
            
        # Check if this line looks like a header
        is_likely_header = (
            len(stripped) < 100 and                    # Not too long
            not stripped.endswith('.') and             # Doesn't end with period
            not re.match(r'^[\-\*\+•]\s+', stripped) and  # Not a list item
            not re.match(r'^\d+[\.\)]\s+', stripped) and   # Not a numbered item
            (
                # Line is all caps
                stripped.isupper() or
                # Line has title case
                stripped.istitle() or
                # Line is surrounded by bold markers
                (stripped.startswith('**') and stripped.endswith('**')) or
                # Next line is empty (section break)
                (i + 1 < len(lines) and not lines[i + 1].strip())
            )
        )
        
        if is_likely_header:
            # Remove existing bold markers
            clean_header = re.sub(r'^\*\*(.*?)\*\*$', r'\1', stripped)
            clean_header = clean_header.strip()
            
            # Determine header level based on context and length
            if len(clean_header) < 30 and (clean_header.isupper() or clean_header.istitle()):
                enhanced_lines.append(f"#### {clean_header}")
            else:
                enhanced_lines.append(f"#### {clean_header}")
        else:
            enhanced_lines.append(line)
    
    return '\n'.join(enhanced_lines)

def _enhance_lists(text: str) -> str:
    """Improve list formatting and detection."""
    # Normalize bullet points
    bullet_patterns = [
        (r'^[•·▪▫‣⁃]\s+', '- '),
        (r'^[◦◦]\s+', '  - '),  # Sub-bullets
        (r'^[\-\*\+]\s+', '- '),
        (r'^(\d+)[\.\)]\s+', r'\1. '),  # Numbered lists
    ]
    
    lines = text.split('\n')
    enhanced_lines = []
    
    for line in lines:
        enhanced_line = line
        
        for pattern, replacement in bullet_patterns:
            enhanced_line = re.sub(pattern, replacement, enhanced_line, flags=re.MULTILINE)
        
        enhanced_lines.append(enhanced_line)
    
    return '\n'.join(enhanced_lines)

def _clean_links_and_formatting(text: str) -> str:
    """Clean up links and text formatting."""
    text = fix_broken_formatting(text)
    
    # Convert markdown links that are just URLs to cleaner format
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', lambda m: 
                  f"[{m.group(1)}]({m.group(2)})" if m.group(1) != m.group(2) 
                  else m.group(2), text)
    
    # Clean up excessive emphasis
    text = re.sub(r'\*\*\*\*(.*?)\*\*\*\*', r'**\1**', text)  # Quadruple to double
    text = re.sub(r'___(.*?)___', r'**\1**', text)            # Triple underscore to bold
    text = re.sub(r'__(.*?)__', r'**\1**', text)              # Double underscore to bold
    
    # Fix spacing around emphasis
    text = re.sub(r'\*\*\s+([^*]+?)\s+\*\*', r'**\1**', text)
    text = re.sub(r'\*\s+([^*]+?)\s+\*', r'*\1*', text)
    
    return text

def _final_cleanup(text: str) -> str:
    """Final cleanup and normalization."""
    # Remove trailing whitespace from lines
    lines = text.split('\n')
    cleaned_lines = [line.rstrip() for line in lines]
    text = '\n'.join(cleaned_lines)
    
    # Ensure proper spacing around headers
    text = re.sub(r'\n(#{1,6}\s+.*?)\n', r'\n\n\1\n\n', text)
    
    # Ensure proper spacing around lists
    text = re.sub(r'\n(\s*[-*+]\s+.*?)\n(?![\s\n]*[-*+])', r'\n\1\n\n', text, flags=re.MULTILINE)
    
    # Remove excessive blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Clean up start and end
    text = text.strip()
    
    return text
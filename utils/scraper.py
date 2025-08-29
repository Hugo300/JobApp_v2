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

        # Clean up excessive newlines
        parsed_data['description'] = cleanup_markdown_newlines(description_markdown)

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
            url = f'http://{domain}/jobs/view/{job_id}'
        if 'jobs/search' in url:
            match = re.search(r'\?(currentJobId)\=(.*?)\&', url)
            
            if match:
                job_id = match.group(0) \
                    .split('=')[1] \
                    .replace('&', '') \
                    .strip()
                
                url = f'http://{domain}/jobs/view/{job_id}'
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
    # Create an html2text converter instance.
    # We can customize it to ignore images, links, or specific tags if needed.
    converter = html2text.HTML2Text()
    converter.ignore_links = False
    converter.ignore_images = True
    converter.body_width=0
    
    # Convert the HTML to Markdown
    markdown_text = converter.handle(html_content)
    return markdown_text

def cleanup_markdown_newlines(markdown_text):
    """
    Removes excessive empty lines from a Markdown string.
    
    Args:
        markdown_text (str): The Markdown string to be cleaned.

    Returns:
        str: The cleaned Markdown string with single empty lines between blocks.
    """
    # Use a regex to replace 3 or more consecutive newlines with 2 newlines.
    # This leaves a single blank line between paragraphs.
    cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', markdown_text)
    return cleaned_text.strip()

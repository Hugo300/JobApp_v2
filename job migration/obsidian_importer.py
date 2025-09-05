#!/usr/bin/env python3
"""
Complete solution for importing jobs from Obsidian markdown files
to a Flask job application via HTTP requests with CSRF token handling.
"""

import yaml
import re
import os
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timezone
from urllib.parse import urljoin

from scraper import _clean_and_enhance_markdown

class ObsidianJobImporter:
    """Complete job importer from Obsidian files to Flask app"""
    
    def __init__(self, base_url: str = "http://localhost:7000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.job_mode_mapping = {
            'remote': 'Remote',
            'hybrid': 'Hybrid',
            'on-site': 'On-site',
            'onsite': 'On-site'
        }
        self.location_mapping = {
            'lisboa': 'Portugal',
            'lisbon': 'Portugal',
            'porto': 'Portugal',
            'oporto': 'Portugal',
            'madrid': 'Spain',
            'barcelona': 'Spain',
            'london': 'United Kingdom',
            'paris': 'France',
            'berlin': 'Germany',
            'munich': 'Germany',
            'amsterdam': 'Netherlands',
            'milan': 'Italy',
            'rome': 'Italy',
            'zurich': 'Switzerland',
            'geneva': 'Switzerland'
        }
    
    def parse_obsidian_file(self, file_path: str) -> Optional[Dict]:
        """Parse a single Obsidian markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self._parse_content(content, file_path)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {str(e)}")
            return None
    
    def _parse_content(self, content: str, file_path: str = "") -> Optional[Dict]:
        """Parse the content of a markdown file"""
        try:
            # Split content into parts
            parts = content.split('---')
            if len(parts) < 3:
                print(f"Invalid format in {file_path}: Missing YAML frontmatter")
                return None
            
            # Parse YAML frontmatter
            yaml_content = parts[1].strip()
            frontmatter = yaml.safe_load(yaml_content) if yaml_content else {}
            
            # Get markdown content (everything after second ---)
            markdown_content = '---'.join(parts[2:]).strip()
            
            # Extract job data
            job_data = self._extract_job_data(markdown_content, frontmatter, file_path)
            
            return job_data
            
        except yaml.YAMLError as e:
            print(f"YAML parsing error in {file_path}: {str(e)}")
            return None
        except Exception as e:
            print(f"Error parsing content from {file_path}: {str(e)}")
            return None
    
    def _extract_job_data(self, markdown_content: str, frontmatter: Dict, file_path: str) -> Dict:
        """Extract job data from markdown content and frontmatter"""
        
        # Company name from filename
        company = Path(file_path).stem if file_path else "Unknown Company"
        
        # Extract position/title
        position_match = re.search(r'Position:\s*\*\*(.*?)\*\*', markdown_content)
        title = position_match.group(1).strip() if position_match else ""
        
        # Extract job mode
        mode_match = re.search(r'Mode:\s*\*\*(.*?)\*\*', markdown_content)
        job_mode_raw = mode_match.group(1).strip().lower() if mode_match else ""
        job_mode = self.job_mode_mapping.get(job_mode_raw, job_mode_raw.title())
        
        # Extract office location
        office_match = re.search(r'Office:\s*([^\n]+)', markdown_content)
        office_location = office_match.group(1).strip() if office_match else ""
        
        # Extract job description from callout block
        description = self._extract_job_description(markdown_content)
        
        # Extract URL if present
        url_match = re.search(r'\[Site Page\]\((.*?)\)', markdown_content)
        url = url_match.group(1).strip() if url_match and url_match.group(1).strip() else ""
        
        # Country mapping based on office location
        country = self._map_office_to_country(office_location)
        
        # Create job data dictionary (only fields needed for job creation)
        job_data = {
            'company': company,
            'title': title,
            'description': description,
            'url': url,
            'office_location': office_location,
            'country': country,
            'job_mode': job_mode,
        }
        
        # Remove empty strings to avoid validation issues
        job_data = {k: v for k, v in job_data.items() if v}
        
        # Add metadata for filtering (not sent to job creation)
        job_data['_metadata'] = {
            'status': frontmatter.get('status', ''),
            'last_update': frontmatter.get('lastUpdate', ''),
            'logs': self._extract_logs(markdown_content)
        }
        
        return job_data
    
    def _extract_job_description(self, content: str) -> str:
        """Extract job description from Obsidian callout blocks"""
        
        # Pattern for callout blocks like > [!abstract]- Job Description
        callout_pattern = r'> \[!abstract\]-?\s*Job Description\s*\n((?:> .*\n?)*)'
        match = re.search(callout_pattern, content, re.MULTILINE | re.IGNORECASE)
        
        if match:
            # Extract content inside callout block
            callout_content = match.group(1)
            
            description = callout_content.replace('>', '')

            cleaned_description = _clean_and_enhance_markdown(description)
            description = cleaned_description if cleaned_description else description
                        
            return description
        
        return ""
    
    def _map_office_to_country(self, office_location: str) -> str:
        """Map office location to country"""
        if not office_location:
            return ""
        
        office_lower = office_location.lower().strip()
        return self.location_mapping.get(office_lower, "")
    
    def _extract_logs(self, content: str) -> List[Dict]:
        """Extract log entries from the markdown content"""
        logs = []
        
        # Find the Log section
        log_section_match = re.search(r'## Log\s*\n---\s*\n(.*)', content, re.DOTALL)
        if not log_section_match:
            return logs
        
        log_content = log_section_match.group(1)
        
        # Extract individual log entries
        log_entries = re.findall(r'### (\d{4}-\d{2}-\d{2}):\s*\n((?:- .*\n?)*)', log_content)
        
        for date_str, entry_content in log_entries:
            try:
                # Parse date
                log_date = datetime.strptime(date_str, '%Y-%m-%d')
                
                # Extract log items
                items = []
                for line in entry_content.split('\n'):
                    line = line.strip()
                    if line.startswith('- '):
                        items.append(line[2:].strip())
                
                if items:
                    logs.append({
                        'date': log_date,
                        'entries': items,
                        'note': '\n'.join(items)
                    })
                    
            except ValueError as e:
                print(f"Error parsing date {date_str}: {e}")
                continue
        
        return logs
    
    def parse_directory(self, directory_path: str, file_pattern: str = "*.md") -> List[Dict]:
        """Parse all markdown files in a directory"""
        directory = Path(directory_path)
        
        if not directory.exists():
            print(f"Directory {directory_path} does not exist")
            return []
        
        parsed_jobs = []
        md_files = list(directory.glob(file_pattern))
        
        print(f"Found {len(md_files)} markdown files in {directory_path}")
        
        for file_path in md_files:
            print(f"Parsing {file_path.name}...")
            job_data = self.parse_obsidian_file(str(file_path))
            
            if job_data:
                parsed_jobs.append(job_data)
                print(f"✓ Successfully parsed: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            else:
                print(f"✗ Failed to parse: {file_path.name}")
        
        return parsed_jobs
    
    def filter_jobs_for_import(self, jobs: List[Dict], status_filter: Optional[List[str]] = None) -> List[Dict]:
        """Filter jobs based on status for import"""
        if not status_filter:
            # Default: exclude jobs with certain statuses
            status_filter = ['open', 'applied', 'interview', 'pending', 'nope', 'rejected', 'closed', 'withdrawn']
        
        filtered_jobs = []
        for job in jobs:
            if isinstance(job.get('_metadata', {}).get('status'), list):
                status_list = job['_metadata']['status']
                job['_metadata']['status'] = status_list[0] if status_list else ''

            job_status = job.get('_metadata', {}).get('status', '').lower()
            
            if not status_filter or job_status in [s.lower() for s in status_filter]:
                filtered_jobs.append(job)
        
        return filtered_jobs
    
    def _extract_csrf_token(self, html_content: str) -> Optional[str]:
        """Extract CSRF token from HTML form"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Method 1: Look for input with name="csrf_token"
        csrf_input = soup.find('input', {'name': 'csrf_token'})
        if csrf_input and csrf_input.get('value'):
            return csrf_input['value']
        
        # Method 2: Look for meta tag with csrf token
        csrf_meta = soup.find('meta', {'name': 'csrf-token'})
        if csrf_meta and csrf_meta.get('content'):
            return csrf_meta['content']
        
        # Method 3: Regex search for common CSRF patterns
        patterns = [
            r'name=["\']csrf_token["\'][^>]*value=["\']([^"\']+)["\']',
            r'value=["\']([^"\']+)["\'][^>]*name=["\']csrf_token["\']',
            r'"csrf_token":\s*"([^"]+)"',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html_content, re.I)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_error_messages(self, html_content: str) -> List[str]:
        """Extract error messages from the returned HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        error_messages = []
        
        # Look for common error message patterns
        error_selectors = [
            '.alert-danger',
            '.error-message',
            '.field-error',
            '.invalid-feedback',
            '[role="alert"]'
        ]
        
        for selector in error_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                if text and text not in error_messages:
                    error_messages.append(text)
        
        return error_messages
    
    def debug_job_data(self, job_data: Dict) -> None:
        """Debug method to inspect job data before sending"""
        print(f"\n=== DEBUG: Job Data for {job_data.get('company', 'Unknown')} ===")
        for key, value in job_data.items():
            if key == 'description':
                print(f"{key}: {len(value)} characters")
                # Show first and last 100 chars to check for issues
                if len(value) > 200:
                    print(f"  Start: {repr(value[:100])}")
                    print(f"  End: {repr(value[-100:])}")
                else:
                    print(f"  Full: {repr(value)}")
            else:
                print(f"{key}: {repr(value)}")
        print("=" * 50)

    def create_jobs_via_http(self, jobs: List[Dict], debug: bool = False) -> Tuple[List[Dict], List[str]]:
        """Create jobs by making POST requests to the Flask app"""
        created_jobs = []
        errors = []
        
        if not jobs:
            return created_jobs, ["No jobs to create"]
        
        try:           
            # Step 1: Get the new job form to extract CSRF token
            form_url = urljoin(self.base_url, "/job/new_job")
            print(f"Fetching CSRF token from: {form_url}")
            
            form_response = self.session.get(form_url, timeout=30)  
            if form_response.status_code != 200:
                return [], [f"Failed to fetch new job form: HTTP {form_response.status_code}"]
            
            # Step 2: Extract CSRF token
            csrf_token = self._extract_csrf_token(form_response.text)
            if not csrf_token:
                return [], ["Could not extract CSRF token from form"]
            
            print(f"Extracted CSRF token: {csrf_token[:20]}...")
            
            # Step 3: Create each job
            submit_url = urljoin(self.base_url, "/job/new_job")
            
            for i, job_data in enumerate(jobs):
                try:
                    if debug:
                        self.debug_job_data(job_data)
                    
                    print(f"\nCreating job {i+1}/{len(jobs)}: {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
                    
                    # Prepare form data
                    form_data = {
                        'csrf_token': csrf_token,
                        'company': job_data.get('company', ''),
                        'title': job_data.get('title', ''),
                        'description': job_data.get('description', ''),
                        'url': job_data.get('url', ''),
                        'office_location': job_data.get('office_location', ''),
                        'country': job_data.get('country', ''),
                        'job_mode': job_data.get('job_mode', ''),
                    }
                    
                    # Remove empty fields to avoid validation issues
                    form_data = {k: v for k, v in form_data.items() if v or k == 'csrf_token'}
                    
                    # Make the POST request
                    response = self.session.post(
                        submit_url,
                        data=form_data,
                        allow_redirects=False,
                        headers={
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Referer': form_url
                        },  
                        timeout=30    
                    )
                    
                    # Check response
                    if response.status_code == 302:
                        # Redirect indicates success
                        location = response.headers.get('Location', '')
                        if location:
                            # Extract job ID from redirect URL
                            job_id_match = re.search(r'/job/(\d+)', location)
                            job_id = job_id_match.group(1) if job_id_match else None
                            
                            job_info = {
                                'title': job_data.get('title'),
                                'company': job_data.get('company'),
                                'redirect_url': location,
                                'job_id': job_id
                            }
                            created_jobs.append(job_info)
                            
                            # Create job logs if they exist in the original data
                            if job_id and '_metadata' in job_data and job_data['_metadata']['logs']:
                                print(f"  Creating {len(job_data['_metadata']['logs'])} log entries...")
                                log_count, log_errors = self.create_job_logs(
                                    job_id, 
                                    job_data['_metadata']['logs'], 
                                    csrf_token
                                )
                                if log_count > 0:
                                    print(f"  ✓ Created {log_count} log entries")
                                if log_errors:
                                    errors.extend(log_errors)
                            
                            print(f"✓ Successfully created: {job_data.get('title')} at {job_data.get('company')}")
                        else:
                            errors.append(f"Unexpected redirect for {job_data.get('title')}: {location}")
                            
                    elif response.status_code == 200:
                        # Form was returned with errors
                        error_messages = self._extract_error_messages(response.text)
                        error_msg = f"Validation failed for {job_data.get('title')}: {'; '.join(error_messages) if error_messages else 'Unknown validation error'}"
                        errors.append(error_msg)
                        print(f"✗ {error_msg}")
                        
                    else:
                        error_msg = f"HTTP {response.status_code} for {job_data.get('title')}"
                        errors.append(error_msg)
                        print(f"✗ {error_msg}")
                    
                    # Get fresh CSRF token for next request
                    if i < len(jobs) - 1:  # Not the last job
                        fresh_token = self._get_fresh_csrf_token(form_url)
                        if fresh_token:
                            csrf_token = fresh_token
                        
                except requests.RequestException as e:
                    error_msg = f"Request error for {job_data.get('title', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    print(f"✗ {error_msg}")
                except Exception as e:
                    error_msg = f"Unexpected error for {job_data.get('title', 'Unknown')}: {str(e)}"
                    errors.append(error_msg)
                    print(f"✗ {error_msg}")
                    
        except Exception as e:
            return [], [f"Session setup error: {str(e)}"]
        
        return created_jobs, errors
    
    def create_job_logs(self, job_id: str, logs: List[Dict], csrf_token: str) -> Tuple[int, List[str]]:
        """Create job logs for a specific job"""
        if not logs:
            return 0, []
        
        created_count = 0
        errors = []
        
        # Sort logs by date to maintain chronological order
        sorted_logs = sorted(logs, key=lambda x: x['date'])

        # Use the detailed log route instead of quick log
        log_url = urljoin(self.base_url, f"/job/{job_id}/add-log")

        response = self.session.post(
            log_url,
            data={
                'csrf_token': csrf_token,
                'note': 'Imported job from obsidian note',
                'created_at': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
            },
            allow_redirects=False,
            headers={
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        )
        
        if response.status_code == 302:
            # Redirect indicates success
            created_count += 1
            print(f"  ✓ Created log entry for data import")
        else:
            error_msg = f"Failed to create log for  data import: HTTP {response.status_code}"
            errors.append(error_msg)
            print(f"  ✗ {error_msg}")
        
        for log_entry in sorted_logs:
            try:
                # Prepare form data for log creation
                form_data = {
                    'csrf_token': csrf_token,
                    'note': log_entry['note'],
                    'created_at': log_entry['date'].strftime('%Y-%m-%d'),
                }
                
                response = self.session.post(
                    log_url,
                    data=form_data,
                    allow_redirects=False,
                    headers={
                        'Content-Type': 'application/x-www-form-urlencoded',
                    }
                )
                
                if response.status_code == 302:
                    # Redirect indicates success
                    created_count += 1
                    print(f"  ✓ Created log entry for {log_entry['date'].strftime('%Y-%m-%d')}")
                else:
                    error_msg = f"Failed to create log for {log_entry['date'].strftime('%Y-%m-%d')}: HTTP {response.status_code}"
                    errors.append(error_msg)
                    print(f"  ✗ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error creating log for {log_entry['date'].strftime('%Y-%m-%d')}: {str(e)}"
                errors.append(error_msg)
                print(f"  ✗ {error_msg}")
        
        return created_count, errors
    
    def _get_fresh_csrf_token(self, form_url: str) -> Optional[str]:
        """Get a fresh CSRF token"""
        try:
            response = self.session.get(form_url)
            if response.status_code == 200:
                return self._extract_csrf_token(response.text)
        except (requests.RequestException, Exception) as e:
            print(f"Failed to get fresh CSRF token: {str(e)}")
        return None

    def import_jobs(self, source_path: str, status_filter: Optional[List[str]] = None, debug: bool = False) -> Dict:
        """
        Complete job import process
        
        Args:
            source_path: Path to directory or single file
            status_filter: List of statuses to include (e.g., ['open', 'applied'])
        
        Returns:
            Dictionary with results summary
        """
        print("=== Starting Job Import Process ===")
        
        # Step 1: Parse files
        source = Path(source_path)
        if source.is_file():
            print(f"Parsing single file: {source_path}")
            parsed_job = self.parse_obsidian_file(source_path)
            parsed_jobs = [parsed_job] if parsed_job else []
        elif source.is_dir():
            print(f"Parsing directory: {source_path}")
            parsed_jobs = self.parse_directory(source_path)
        else:
            return {'error': f"Path does not exist: {source_path}"}
        
        if not parsed_jobs:
            return {'error': 'No jobs could be parsed from the source'}
        
        print(f"Parsed {len(parsed_jobs)} jobs from files")
        
        # Step 2: Filter jobs
        filtered_jobs = self.filter_jobs_for_import(parsed_jobs, status_filter)
        print(f"Filtered to {len(filtered_jobs)} jobs for import")
        
        if not filtered_jobs:
            return {
                'parsed': len(parsed_jobs),
                'filtered': 0,
                'message': 'No jobs match the status filter criteria'
            }
        
        # Step 4: Create jobs via HTTP
        print(f"\nCreating {len(filtered_jobs)} jobs...")
        created_jobs, errors = self.create_jobs_via_http(filtered_jobs, debug=debug)
        
        # Step 5: Summary
        summary = {
            'parsed': len(parsed_jobs),
            'filtered': len(filtered_jobs),
            'created': len(created_jobs),
            'failed': len(errors),
            'success_rate': f"{(len(created_jobs)/len(filtered_jobs)*100):.1f}%" if filtered_jobs else "0%",
            'created_jobs': created_jobs,
            'errors': errors
        }
        
        print(f"\n=== Import Summary ===")
        print(f"Parsed: {summary['parsed']} jobs")
        print(f"Filtered: {summary['filtered']} jobs")
        print(f"Created: {summary['created']} jobs")
        print(f"Failed: {summary['failed']} jobs")
        print(f"Success rate: {summary['success_rate']}")
        
        if created_jobs:
            print(f"\n✓ Successfully created jobs:")
            for job in created_jobs:
                print(f"  - {job['title']} at {job['company']}")
        
        if errors:
            print(f"\n✗ Errors:")
            for error in errors[:10]:  # Show first 10 errors
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")
        
        return summary
    
    def close(self):
        """Close the session"""
        self.session.close()


def main():
    """Example usage and CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import jobs from Obsidian markdown files')
    parser.add_argument('source', help='Path to directory or single markdown file')
    parser.add_argument('--base-url', default='http://localhost:7000', 
                       help='Base URL of the Flask application')
    parser.add_argument('--status-filter', nargs='+', 
                       help='Status values to include (e.g., open applied)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Parse and filter jobs but do not create them')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug output to inspect job data')

    args = parser.parse_args()
    
    # Create importer
    importer = ObsidianJobImporter(base_url=args.base_url)
    
    try:
        if args.dry_run:
            # Just parse and show what would be imported
            source = Path(args.source)
            if source.is_file():
                parsed_jobs = [importer.parse_obsidian_file(args.source)]
                parsed_jobs = [job for job in parsed_jobs if job]
            else:
                parsed_jobs = importer.parse_directory(args.source)
            
            filtered_jobs = parsed_jobs
            
            print(f"=== Dry Run Results ===")
            print(f"Parsed: {len(parsed_jobs)} jobs")
            print(f"Would import: {len(filtered_jobs)} jobs")
            
            if filtered_jobs:
                print(f"\nJobs that would be created:")
                for job in filtered_jobs:
                    print(f"  - {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}")

                    if args.debug:
                        if '_metadata' in job and 'logs' in job['_metadata']:
                            print(job['_metadata']['logs'])
            
        else:
            # Run the full import
            result = importer.import_jobs(
                source_path=args.source,
                status_filter=args.status_filter,
            )
            
            if 'error' in result:
                print(f"Error: {result['error']}")
                return 1
            
            return 0 if result['failed'] == 0 else 1
            
    finally:
        importer.close()


if __name__ == "__main__":
    exit(main())
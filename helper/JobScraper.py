import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from helper.url_converter import string_to_url
from helper.csv_generator import generate_csv

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class InternshalaJobScraper:
    def __init__(self):
        self.base_url = "https://internshala.com"
        self.session = self._create_session()
        
    def _create_session(self):
        """Create a session with proper headers and retry strategy."""
        session = requests.Session()
        
        # Set headers to appear more like a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        session.headers.update(headers)
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_page(self, url, timeout=10):
        """
        Get page content with error handling.
        
        Args:
            url (str): URL to fetch
            timeout (int): Request timeout in seconds
            
        Returns:
            requests.Response or None: Response object or None if failed
        """
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def _safe_find_text(self, soup_element, selector_type, selector, default="N/A"):
        """
        Safely extract text from BeautifulSoup element.
        
        Args:
            soup_element: BeautifulSoup element to search in
            selector_type (str): Type of selector ('class', 'tag', 'id', etc.)
            selector: The selector value
            default (str): Default value if not found
            
        Returns:
            str: Extracted text or default value
        """
        try:
            if selector_type == 'class':
                element = soup_element.find(class_=selector)
            elif selector_type == 'tag':
                element = soup_element.find(selector)
            elif selector_type == 'id':
                element = soup_element.find(id=selector)
            else:
                element = soup_element.find(selector)
            
            if element:
                text = element.get_text(strip=True)
                return text if text else default
            return default
        except Exception as e:
            logger.debug(f"Error extracting text with selector {selector}: {e}")
            return default
    
    def _extract_job_data(self, job_element):
        """
        Extract job data from a job listing element.
        
        Args:
            job_element: BeautifulSoup element containing job info
            
        Returns:
            dict: Dictionary containing job information
        """
        job_data = {}
        
        try:
            # Try multiple selectors for different page layouts
            
            # Company name - try different selectors
            company_selectors = [
                ('class', 'company_name'),
                ('class', 'company'),
                ('tag', 'h3'),
                ('class', 'heading_4_5 profile'),
                ('class', 'profile_name')
            ]
            
            for sel_type, selector in company_selectors:
                company_name = self._safe_find_text(job_element, sel_type, selector, "")
                if company_name and company_name != "N/A":
                    # Clean company name properly
                    job_data['company_name'] = ' '.join(company_name.split())
                    break
            
            if not job_data.get('company_name'):
                job_data['company_name'] = "N/A"
            
            # Job title - try different selectors
            title_selectors = [
                ('class', 'profile'),
                ('class', 'job-title'),
                ('class', 'profile_name'),
                ('tag', 'h4')
            ]
            
            for sel_type, selector in title_selectors:
                job_title = self._safe_find_text(job_element, sel_type, selector, "")
                if job_title and job_title != "N/A":
                    job_data['job_title'] = job_title
                    break
            
            if not job_data.get('job_title'):
                job_data['job_title'] = "N/A"
            
            # Location - try different selectors
            location_selectors = [
                ('class', 'location_link'),
                ('class', 'locations'),
                ('class', 'location')
            ]
            
            for sel_type, selector in location_selectors:
                location = self._safe_find_text(job_element, sel_type, selector, "")
                if location and location != "N/A":
                    job_data['company_location'] = location
                    break
            
            if not job_data.get('company_location'):
                job_data['company_location'] = "N/A"
            
            # Salary/Stipend
            salary_selectors = [
                ('class', 'stipend'),
                ('class', 'salary'),
                ('class', 'other_detail_item')
            ]
            
            for sel_type, selector in salary_selectors:
                salary = self._safe_find_text(job_element, sel_type, selector, "")
                if salary and salary != "N/A":
                    # Clean salary text
                    salary = salary.replace('₹', '').replace(',', '').strip()
                    job_data['job_salary'] = salary
                    break
            
            if not job_data.get('job_salary'):
                job_data['job_salary'] = "Not specified"
            
            # Job type/category
            type_selectors = [
                ('class', 'job_type'),
                ('class', 'other_label'),
                ('class', 'internship_type')
            ]
            
            for sel_type, selector in type_selectors:
                job_type = self._safe_find_text(job_element, sel_type, selector, "")
                if job_type and job_type != "N/A":
                    job_data['job_type'] = job_type
                    break
            
            if not job_data.get('job_type'):
                job_data['job_type'] = "Not specified"
            
            # Duration
            duration_selectors = [
                ('class', 'duration'),
                ('class', 'other_detail_item')
            ]
            
            for sel_type, selector in duration_selectors:
                duration = self._safe_find_text(job_element, sel_type, selector, "")
                if duration and duration != "N/A" and 'month' in duration.lower():
                    job_data['job_duration'] = duration
                    break
            
            if not job_data.get('job_duration'):
                job_data['job_duration'] = "Not specified"
            
            # Job detail link
            link_element = job_element.find('a', href=True)
            if link_element:
                href = link_element['href']
                if href.startswith('/'):
                    job_data['job_link'] = urljoin(self.base_url, href)
                else:
                    job_data['job_link'] = href
            else:
                job_data['job_link'] = "N/A"
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            # Return partial data with defaults
            for key in ['company_name', 'job_title', 'company_location', 'job_salary', 'job_type', 'job_duration', 'job_link']:
                if key not in job_data:
                    job_data[key] = "N/A"
        
        return job_data
    
    def scrape_jobs(self, position, location, max_pages=3):
        """
        Scrape jobs from Internshala.
        
        Args:
            position (str): Job position to search for
            location (str): Location to search in
            max_pages (int): Maximum number of pages to scrape
            
        Returns:
            list: List of job dictionaries
        """
        all_jobs = []
        
        # Construct URL
        position_url = string_to_url(position)
        location_url = string_to_url(location)
        base_search_url = f"{self.base_url}/internships/{position_url}-internship-in-{location_url}"
        
        for page in range(1, max_pages + 1):
            if page == 1:
                url = base_search_url
            else:
                url = f"{base_search_url}/page-{page}"
            
            logger.info(f"Scraping page {page}: {url}")
            
            response = self._get_page(url)
            if not response:
                logger.warning(f"Failed to fetch page {page}")
                continue
            
            soup = BeautifulSoup(response.text, 'lxml')
            
            # Try different selectors for job listings
            job_selectors = [
                'div.internship_meta',
                'div.individual_internship',
                'div.container-fluid',
                'div.job-card',
                '.search_results .internship_meta'
            ]
            
            jobs = []
            for selector in job_selectors:
                jobs = soup.select(selector)
                if jobs:
                    logger.info(f"Found {len(jobs)} job listings using selector: {selector}")
                    break
            
            if not jobs:
                logger.warning(f"No job listings found on page {page}")
                if page == 1:
                    # Try to find any div that might contain jobs
                    potential_jobs = soup.find_all('div', {'class': True})
                    logger.info(f"Found {len(potential_jobs)} divs with classes on the page")
                    
                    # Print first few class names for debugging
                    for i, div in enumerate(potential_jobs[:10]):
                        classes = ' '.join(div.get('class', []))
                        logger.debug(f"Div {i}: classes = {classes}")
                break
            
            page_jobs = []
            for job_element in jobs:
                job_data = self._extract_job_data(job_element)
                
                # Only add if we got meaningful data
                if (job_data.get('company_name', 'N/A') != 'N/A' or 
                    job_data.get('job_title', 'N/A') != 'N/A'):
                    page_jobs.append(job_data)
            
            all_jobs.extend(page_jobs)
            logger.info(f"Extracted {len(page_jobs)} jobs from page {page}")
            
            # Be respectful - add delay between requests
            if page < max_pages:
                time.sleep(2)
        
        return all_jobs

def scrape_internshala_jobs(position, location):
    """
    Main function to scrape Internshala jobs.
    
    Args:
        position (str): Job position to search for
        location (str): Location to search in
    """
    scraper = InternshalaJobScraper()
    
    try:
        jobs = scraper.scrape_jobs(position, location)
        
        if not jobs:
            print("\nNo jobs found. This could be due to:")
            print("1. No matching internships available")
            print("2. Website structure has changed")
            print("3. Network or access issues")
            print("4. Search terms may need adjustment")
            return
        
        print(f"\nFound {len(jobs)} internship(s):")
        print("=" * 60)
        
        for i, job in enumerate(jobs, 1):
            print(f"\n{i}. {job['job_title']}")
            print(f"   Company: {job['company_name']}")
            print(f"   Location: {job['company_location']}")
            print(f"   Salary: {job['job_salary']}")
            print(f"   Type: {job['job_type']}")
            print(f"   Duration: {job['job_duration']}")
            print(f"   Link: {job['job_link']}")
        
        # Ask user if they want to save to CSV
        print("\n" + "=" * 60)
        while True:
            try:
                save_choice = input("Save results to CSV file? (y/n): ").strip().lower()
                if save_choice in ['y', 'yes']:
                    filename = generate_csv(jobs)
                    if filename:
                        print(f"Data saved to {filename}")
                    break
                elif save_choice in ['n', 'no']:
                    print("Results not saved.")
                    break
                else:
                    print("Please enter 'y' for yes or 'n' for no.")
            except KeyboardInterrupt:
                print("\nExiting...")
                break
        
    except Exception as e:
        logger.error(f"Error during scraping: {e}")
        print(f"An error occurred during scraping: {e}")
    
    print("\nThank you for using Internshala Job Scraper!")

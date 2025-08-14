import streamlit as st
import requests
from bs4 import BeautifulSoup
import time
import logging
import csv
import os
import urllib.parse
from datetime import datetime
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import io

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Internshala Job Scraper",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

def string_to_url(text):
    """
    Convert a string to URL-safe format.
    
    Args:
        text (str): The text to convert
        
    Returns:
        str: URL-safe string
    """
    if not text:
        return ""
    
    # Clean and encode the text properly
    text = text.strip().lower()
    # Replace spaces with hyphens for Internshala URL format
    text = text.replace(' ', '-')
    # URL encode any special characters
    text = urllib.parse.quote(text, safe='-')
    
    return text

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)

def generate_csv_data(job_data_list):
    """
    Generate CSV data from job data list.
    
    Args:
        job_data_list (list): List of dictionaries containing job data
        
    Returns:
        str: CSV data as string
    """
    if not job_data_list:
        return None
    
    # Create CSV in memory
    output = io.StringIO()
    
    # Define CSV headers
    headers = ['Company_Name', 'Company_Location', 'Job_Title', 'Job_Salary', 
              'Job_Type', 'Job_Duration', 'Job_Detail_URL']
    
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    
    for job in job_data_list:
        # Ensure all required fields exist
        row = {
            'Company_Name': job.get('company_name', 'N/A'),
            'Company_Location': job.get('company_location', 'N/A'),
            'Job_Title': job.get('job_title', 'N/A'),
            'Job_Salary': job.get('job_salary', 'N/A'),
            'Job_Type': job.get('job_type', 'N/A'),
            'Job_Duration': job.get('job_duration', 'N/A'),
            'Job_Detail_URL': job.get('job_link', 'N/A')
        }
        writer.writerow(row)
    
    return output.getvalue()

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
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching {url}: {e}")
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
    
    def scrape_jobs(self, position, location, max_pages=3, progress_callback=None):
        """
        Scrape jobs from Internshala.
        
        Args:
            position (str): Job position to search for
            location (str): Location to search in
            max_pages (int): Maximum number of pages to scrape
            progress_callback: Function to call for progress updates
            
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
            
            if progress_callback:
                progress_callback(f"Scraping page {page} of {max_pages}...")
            
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

def main():
    """Main Streamlit application."""
    
    # Header
    st.title("💼 Internshala Job Scraper")
    st.markdown("---")
    
    # Sidebar for inputs
    with st.sidebar:
        st.header("Search Parameters")
        
        position = st.text_input(
            "Job Position",
            placeholder="e.g., Python Developer, Data Science, Marketing",
            help="Enter the job position you're looking for"
        )
        
        location = st.text_input(
            "Location",
            placeholder="e.g., Delhi, Mumbai, Bangalore",
            help="Enter the city or location"
        )
        
        max_pages = st.slider(
            "Max Pages to Scrape",
            min_value=1,
            max_value=5,
            value=2,
            help="Number of pages to scrape (more pages = more results but longer wait time)"
        )
        
        scrape_button = st.button("🔍 Start Scraping", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Instructions")
        st.markdown("""
        1. Enter the job position you're looking for
        2. Specify the location 
        3. Choose how many pages to scrape
        4. Click 'Start Scraping' to begin
        5. Results will appear in the main area
        6. Download CSV when ready
        """)
    
    # Main content area
    if scrape_button:
        if not position or not location:
            st.error("⚠️ Please fill in both position and location fields.")
            return
        
        # Initialize scraper
        scraper = InternshalaJobScraper()
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(message):
            status_text.text(message)
        
        # Start scraping
        st.info(f"🔍 Searching for '{position}' positions in '{location}'...")
        
        try:
            jobs = scraper.scrape_jobs(
                position, 
                location, 
                max_pages, 
                progress_callback=update_progress
            )
            
            progress_bar.progress(100)
            status_text.text("✅ Scraping completed!")
            
            if not jobs:
                st.warning("❌ No jobs found. This could be due to:")
                st.markdown("""
                - No matching internships available
                - Website structure may have changed
                - Network or access issues
                - Search terms may need adjustment
                """)
                return
            
            # Display results
            st.success(f"🎉 Found {len(jobs)} internship(s)!")
            
            # Convert to DataFrame for better display
            df_jobs = []
            for i, job in enumerate(jobs, 1):
                df_jobs.append({
                    'S.No': i,
                    'Job Title': job['job_title'],
                    'Company': job['company_name'],
                    'Location': job['company_location'],
                    'Salary': job['job_salary'],
                    'Type': job['job_type'],
                    'Duration': job['job_duration'],
                    'Link': job['job_link']
                })
            
            df = pd.DataFrame(df_jobs)
            
            # Display results in tabs
            tab1, tab2 = st.tabs(["📋 Table View", "📊 Summary"])
            
            with tab1:
                st.subheader("Job Listings")
                
                # Make links clickable in the dataframe
                def make_clickable(url):
                    if url != "N/A" and url.startswith('http'):
                        return f'<a href="{url}" target="_blank">View Job</a>'
                    return url
                
                df_display = df.copy()
                df_display['Link'] = df_display['Link'].apply(make_clickable)
                
                st.write(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)
            
            with tab2:
                st.subheader("Summary Statistics")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Jobs Found", len(jobs))
                
                with col2:
                    unique_companies = len(df[df['Company'] != 'N/A']['Company'].unique())
                    st.metric("Unique Companies", unique_companies)
                
                with col3:
                    paid_jobs = len(df[df['Salary'] != 'Not specified'])
                    st.metric("Jobs with Salary Info", paid_jobs)
                
                # Company distribution
                if unique_companies > 0:
                    st.subheader("Top Companies")
                    company_counts = df[df['Company'] != 'N/A']['Company'].value_counts().head(10)
                    st.bar_chart(company_counts)
                
                # Location distribution
                location_counts = df[df['Location'] != 'N/A']['Location'].value_counts().head(10)
                if len(location_counts) > 0:
                    st.subheader("Top Locations")
                    st.bar_chart(location_counts)
            
            # Download section
            st.markdown("---")
            st.subheader("📥 Download Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Generate CSV data
                csv_data = generate_csv_data(jobs)
                if csv_data:
                    st.download_button(
                        label="📊 Download as CSV",
                        data=csv_data,
                        file_name=f"internshala_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            
            with col2:
                # Generate Excel data
                excel_buffer = io.BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    df.to_excel(writer, sheet_name='Jobs', index=False)
                
                st.download_button(
                    label="📈 Download as Excel",
                    data=excel_buffer.getvalue(),
                    file_name=f"internshala_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            
        except Exception as e:
            st.error(f"❌ An error occurred during scraping: {str(e)}")
            logger.error(f"Error during scraping: {e}")
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to Internshala Job Scraper! 👋
        
        This tool helps you scrape job listings from Internshala with ease. Here's what you can do:
        
        ### ✨ Features:
        - 🔍 Search for specific job positions
        - 📍 Filter by location
        - 📊 View results in table format
        - 📈 Get summary statistics
        - 💾 Download results as CSV or Excel
        - 🔄 Multi-page scraping support
        
        ### 🚀 How to Use:
        1. Use the sidebar to enter your search criteria
        2. Click "Start Scraping" to begin
        3. View results and download data
        
        ### ⚠️ Important Notes:
        - This tool respects rate limits and includes delays between requests
        - Results may vary based on website structure changes
        - Use responsibly and respect Internshala's terms of service
        
        **Ready to start? Fill in the form in the sidebar! 👈**
        """)

if __name__ == "__main__":
    main()

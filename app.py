import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import io

def string_to_url(text):
    """Convert string to URL format"""
    text = text.strip().replace(' ', '%20')
    return text

def scrape_internshala(position, location):
    """Scrape job data from Internshala"""
    try:
        url = f'https://internshala.com/internships/{string_to_url(position)}-internship-in-{string_to_url(location)}/'
        
        # Add headers to avoid being blocked
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'lxml')
        jobs = soup.findAll('div', class_='container-fluid individual_internship visibilityTrackerItem')
        
        job_data = []
        
        if len(jobs) == 0:
            return None, "No jobs found. Please check your search criteria."
        
        for job in jobs:
            try:
                # Extract company info
                company_info = job.find('div', class_='company_and_premium')
                if not company_info:
                    continue
                    
                company_name = company_info.a.text.strip() if company_info.a else "N/A"
                
                # Extract job title
                jobtitle_div = job.find('div', class_='company')
                job_title = jobtitle_div.a.text.strip() if jobtitle_div and jobtitle_div.a else "N/A"
                
                # Extract location
                location_link = job.find('a', class_='location_link view_detail_button')
                company_location = location_link.text.strip() if location_link else "N/A"
                
                # Extract job link
                cta_container = job.find('div', class_='cta_container')
                if cta_container and cta_container.a:
                    job_link = 'https://internshala.com' + cta_container.a['href']
                else:
                    job_link = "N/A"
                
                # Extract salary
                try:
                    salary_span = job.find('span', class_='stipend')
                    job_salary = salary_span.text.replace("₹", "").replace(",", "").strip() if salary_span else "Not specified"
                except:
                    job_salary = "Not specified"
                
                # Extract job type
                try:
                    job_type_div = job.find('div', class_='other_label_container')
                    job_type = job_type_div.div.div.text.strip() if job_type_div and job_type_div.div and job_type_div.div.div else "Not specified"
                except:
                    job_type = "Not specified"
                
                job_data.append({
                    'Company Name': company_name,
                    'Location': company_location,
                    'Job Title': job_title,
                    'Salary': job_salary,
                    'Job Type': job_type,
                    'Job Link': job_link
                })
                
            except Exception as e:
                st.warning(f"Error processing a job listing: {str(e)}")
                continue
        
        return job_data, None
        
    except requests.RequestException as e:
        return None, f"Network error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"

def generate_csv_download(df):
    """Generate CSV file for download"""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False, encoding='utf-8')
    return csv_buffer.getvalue()

def main():
    st.set_page_config(
        page_title="Job & Internship Finder",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Job & Internship Finder")
    st.subheader("Search Jobs & Internships from Internshala")
    
    # Sidebar for search parameters
    st.sidebar.header("Search Parameters")
    
    with st.sidebar:
        position = st.text_input(
            "Job Position",
            placeholder="e.g., Python Developer, Data Analyst",
            help="Enter the job position you're looking for"
        )
        
        location = st.text_input(
            "Location",
            placeholder="e.g., Delhi, Mumbai, Bangalore",
            help="Enter the city where you want to search for jobs"
        )
        
        search_button = st.button("🔍 Search Jobs", type="primary")
    
    # Main content area
    if search_button:
        if not position or not location:
            st.error("Please enter both job position and location.")
            return
        
        with st.spinner(f"Searching for {position} jobs in {location}..."):
            job_data, error = scrape_internshala(position, location)
        
        if error:
            st.error(error)
            st.info("Tips for better results:")
            st.write("- Check your spelling")
            st.write("- Try broader search terms")
            st.write("- Use common job titles like 'developer', 'analyst', 'intern'")
            return
        
        if not job_data:
            st.warning("No jobs found for your search criteria.")
            return
        
        # Display results
        st.success(f"Found {len(job_data)} job opportunities!")
        
        # Convert to DataFrame for better display
        df = pd.DataFrame(job_data)
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Jobs", len(df))
        
        with col2:
            unique_companies = df['Company Name'].nunique()
            st.metric("Unique Companies", unique_companies)
        
        with col3:
            paid_jobs = len(df[df['Salary'] != 'Not specified'])
            st.metric("With Salary Info", paid_jobs)
        
        with col4:
            unique_locations = df['Location'].nunique()
            st.metric("Unique Locations", unique_locations)
        
        # Display the data table
        st.subheader("📋 Job Listings")
        
        # Make the job links clickable
        def make_clickable(link):
            if link != "N/A":
                return f'<a href="{link}" target="_blank">View Job</a>'
            return link
        
        df_display = df.copy()
        df_display['Job Link'] = df_display['Job Link'].apply(make_clickable)
        
        st.write(df_display.to_html(escape=False), unsafe_allow_html=True)
        
        # Download section
        st.subheader("💾 Download Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = generate_csv_download(df)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"jobs_{position.replace(' ', '_')}_{location.replace(' ', '_')}_{timestamp}.csv"
            
            st.download_button(
                label="📥 Download as CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv"
            )
        
        with col2:
            # Option to search again
            if st.button("🔄 New Search"):
                st.rerun()
    
    else:
        # Welcome message
        st.info("👋 Welcome! Use the sidebar to search for jobs and internships.")
        
        # Add some helpful information
        st.subheader("How to use:")
        st.write("1. Enter the job position you're looking for (e.g., 'Python Developer')")
        st.write("2. Enter the location (e.g., 'Delhi', 'Mumbai')")
        st.write("3. Click 'Search Jobs' to find opportunities")
        st.write("4. View results and download as CSV if needed")
        
        # Add example searches
        st.subheader("Example Searches:")
        examples = [
            ("Data Analyst", "Bangalore"),
            ("Web Developer", "Mumbai"),
            ("Content Writer", "Delhi"),
            ("Digital Marketing", "Pune")
        ]
        
        for pos, loc in examples:
            st.write(f"• {pos} in {loc}")

if __name__ == "__main__":
    main()

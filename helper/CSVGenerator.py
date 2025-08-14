import csv
import os
from datetime import datetime
import logging

def ensure_directory_exists(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"Created directory: {directory}")

def generate_csv(job_data_list):
    """
    Generate CSV file from job data.
    
    Args:
        job_data_list (list): List of dictionaries containing job data
        
    Returns:
        str: Filename of created CSV file, or None if failed
    """
    if not job_data_list:
        print("No data to save.")
        return None
    
    try:
        # Ensure job_data directory exists
        ensure_directory_exists('job_data')
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'job_data/internshala_jobs_{timestamp}.csv'
        
        # Define CSV headers
        headers = ['Company_Name', 'Company_Location', 'Job_Title', 'Job_Salary', 
                  'Job_Type', 'Job_Duration', 'Job_Detail_URL']
        
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
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
        
        print(f'File saved successfully: {filename}')
        return filename
        
    except Exception as e:
        logging.error(f"Error generating CSV: {e}")
        print(f"Error saving CSV file: {e}")
        return None

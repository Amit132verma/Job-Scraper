from helper.URLConverter import string_to_url
from helper.CSVGenerator import generate_csv
from bs4 import BeautifulSoup
import requests


def scrap_indeed_website(position, location):

    
   
    url = f'https://internshala.com/internships/{string_to_url(position)}-internship-in-{string_to_url(location)}/'
    content = requests.get(url).text
    soup = BeautifulSoup(content, 'lxml')
    
    jobs = soup.findAll('div', class_='container-fluid individual_internship visibilityTrackerItem')
    csv_data = 'Company_Name,Company_Location,Job_Title,Job_Salary,Job_Type,Job_Detail,\n'

    if len(jobs) != 0:
        for job in jobs:
            #job_container = job.find('table', class_='jobCard_mainContent big6_visualChanges')
            #job_detail = job_container.find('div', class_='heading6 tapItem-gutter metadataContainer noJEMChips salaryOnly')
           
            company_info = job.find('div', class_='company_and_premium')


            job_link =job.find('div', class_='cta_container').a['href'] 
            job_link = 'https://internshala.com' + job_link
            
            company_name = company_info.a.text
            company_name = company_name.replace(" ", "")

            jobtitle = job.find('div', class_='company')
            job_title=jobtitle.a.text
            
           
           
            company_location=job.find('a',class_='location_link view_detail_button').text
           

            try:
                job_salary = job.find('span', class_='stipend').text
                job_salary=job_salary.replace("₹", "")
                job_salary=job_salary.replace(",","")

            except:
                job_salary = 'No salary data found'

            try:
                job_type = job.find('div', class_='other_label_container').div.div.text

                # for i in range(len(job_type)):
                #     if i == len(job_type) - 1:
                #         job_type = job_type[i].div.text
            except:
                job_type = 'No job type data found'

            csv_data += f'{company_name},{company_location},{job_title},{job_salary},{job_type},{job_link},\n'

            print(f'Company Name: {company_name}')
            print(f'Company Location: {company_location}')
            print(f'Job Title: {job_title}')
           
            print(f'Job Salary: {job_salary}')
            print(f'Job Type: {job_type}')
            print(f'Job Detail: {job_link}')
            print()

        save_to_csv = ''
        while save_to_csv != 'Y' and save_to_csv != 'n':
            save_to_csv = input('Want to save data to CSV file? [Y/n]: ')
            if save_to_csv == 'Y':
                generate_csv(csv_data)
                print('Thank You!')
            elif save_to_csv == 'n':
                print('Thank You!')
            else:
                print('Input invalid')
    else:
        print('Please make sure the position and location keyword is correct.')
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from helper.job_scraper import scrape_internshala_jobs

if __name__ == '__main__':
    print('Search Job & Internship Via Internshala')
    print('=' * 40)
    
    while True:
        try:
            position = input('Job Position: ').strip()
            if not position:
                print("Position cannot be empty. Please try again.")
                continue
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            exit()
    
    while True:
        try:
            location = input('Location: ').strip()
            if not location:
                print("Location cannot be empty. Please try again.")
                continue
            break
        except KeyboardInterrupt:
            print("\nExiting...")
            exit()
    
    print(f'\nSearching for {position} positions in {location}...')
    print('=' * 50)
    
    scrape_internshala_jobs(position, location)

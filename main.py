from helper.JobScraper import scrap_indeed_website

if __name__ == '__main__':
    print('Search Job & Internship Via Internshala')
    print('===============================')
    position = input('Job Position: ')
    location = input('Location: ')
    print('\nResult')
    print('======')
    scrap_indeed_website(position, location)
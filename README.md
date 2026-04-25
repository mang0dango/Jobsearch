This project speeds up the job application process by helping users find more tailored jobs to their skillset and making applications easier with greenhouse autofill.

Prerequisites & Setup:

- Create a greenhouse.io account.
- Create an autofill profile on greenhouse.
- Install Selenium, Pandas, and Requests for Python.
- Navigate to config.py to change the query parameters as needed to filter for your ideal job.
- Install a Chrome Driver that matches your Chrome Version.
- Run "bash run_\chrome_\Session.sh" in a separate terminal tab.
- A new chrome window should open. It should not be signed in any google accounts. Open greenhouse.io website and sign in with your account (only the first time). Leave this chrome instance running while using fetch_/jobs.py.
- Then you can execute the python scripts in a separate terminal window to generate a list of jobs. 
- Use the list of jobs to apply to under data/approved_/jobs.csv by opening the file in google sheets. 

How does this project work?

Selenium opens a new browser session, you log in with your info (once, just the first time you use this script) and then it automates a job search on the greenhouse website, fetching all job links and going through as many pages of job listings as specified.
Then the job listings are filtered out based on how well they match your skills and job search criteria. Specific words also automatically blacklisted from job listings. You can specify all this in the src/config.py. Once a list of good matches are made, basic information is extracted about each job listing and uploaded to a csv file. Then you can upload this file to google sheets and go through all the links manually, using the apply with greenhouse autofill option to quickly fill most of the answers and manually fill in any unusual or extra question fields. Now you applied to the most relevant roles and saved lots of time filling in the answers and deciding which jobs to apply to.



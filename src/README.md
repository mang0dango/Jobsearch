This project speeds up the job application process by helping users find more tailored jobs to their skillset and making applications easier with greenhouse autofill.

Prerequisites & Setup:

- Create a greenhouse.io account.
- Create an autofill profile on greenhouse.
- Install Selenium, Pandas for Python.
- Change the query parameters as needed to match your ideal job and skills in config.
- Install a Chrome Driver that matches your Chrome Version.
- Run "bash run_\chrome_\Session.sh" in a separate terminal tab.
- A new chrome window should open. It should not be signed in. Open greenhouse.io website and sign in with your account. Leave this chrome instance running.
- Then you can execute the python scripts in a separate terminal window to generate a list of jobs to apply to.

How does this project work?

Selenium opens a new browser session, you log in with your info and then it automates a job search on the greenhouse website, fetching all unique company names and going through as many pages of job listings as specified.
Once the company names are fetched, greenhouse api calls are made with the company name, pulling up all relevant job listings. Then the job listings are given a confidence score of 60% or more as relates to your skills and job search criteria. Specific words also automatically blacklist job listings. You can specify all this in the config. Once a list of good matches are made, basic information is extracted about each job listing and uploaded to a csv file. Then you can upload this file to google sheets and go through all the links manually, using the apply with greenhouse autofill option to quickly fill most of the answers and manually fill in any unusual or extra question fields. Now you applied to the most relevant roles and saved lots of time filling in the answers and deciding which jobs to apply to.


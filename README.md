This project makes applying to jobs fun. Scrape thousands of greenhouse job listings, filter out irrelevant roles, and find the highest skill-based matches. 

How to use this script?

- Navigate to greenhouse.io in the browser and create an account.
- (Optional) Create an autofill applications profile on greenhouse.
- Navigate to src/config.py to change the search parameters as needed to filter for your ideal job.
- Run "./src/start.sh" to execute the script. 
- A new chrome window should open. It should not be signed in to any google accounts or profiles.
- Navigate to the greenhouse.io website and sign in with your account if prompted by the script. 
- Open the "data/approved_/jobs.csv" with google sheets or a similar spreadsheet reader.
- Mark jobs you applied to, date applied, and status updates on the spreadsheet. 
- Once you are ready to search for more jobs, download the spreadsheet as csv again.
- Replace the old "data/approved\_jobs.py" file with the new file to keep your notes in place.
- Execute the "./src/start.sh" file again to rerun the script.

How does this project work?

The setup.sh file (called by startup.sh) installs all needed prerequisites for this script to run.
The startup.sh file then starts a new browser session and starts the "fetch\_jobs.py" file.
The "fetch\_jobs.py" file scrapes all the job listings with selenium from the links you provided and uploads them to "data/fetched\_jobs.csv"
The "filter\_jobs.py" file then filters the job listings to remove irrelevant experience status jobs, jobs with blacklisted terms, and jobs with low skill-based matches.
The results are then uploaded to "data/rejected\_jobs.csv", "data/approved\_jobs,csv", "data/unfiltered\_jobs.csv" (jobs that need manual approval), "and "data/processed\_jobs.csv" (all filtered jobs).


Known Issues:

- the tests need to be updated to match the new code changes.
- the job links need to be normalized by removing redundant link metadata at the end to make the program more efficient and reduce chance of duplicates.

Future Developments:

- switching from pandas and csv to a proper database.
- creating better config options based on work experience level. 
- adding data from more websites such as linkedin, indeed, etc.
- creating an easier-to-use user interface with react.
- importing AI cover letter generator into this project.
- filtering jobs based on "easy apply" vs not.
- adding ML to help with fine tuning the config options and improving match accuracy
  (for now I'm keeping API's out of the project so it can continue being easier to setup and free).
- using AI to fetch skills from the user's linkedin page and resume
  (for now I'm keeping API's out of the project so it can continue being easier to setup and free).
- maybe implimenting an automatic apply feature for the "easy apply" jobs with no long text questions.

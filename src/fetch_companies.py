import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

options = Options() 
options.debugger_address = "127.0.0.1:9222"
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

def load_greenhouse():
    driver.get("https://my.greenhouse.io/jobs?query=software%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote")
    time.sleep(5)
    print("Update: Session loaded successfully")

def load_more_jobs(total_page_expansions: int):
    """ Click the button on the bottom of the page to see more jobs as many times as specified by the function arg. """

    for expansion_number in range(total_page_expansions):
        button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[.//span[text()='See more jobs']]")
            )
        )

        driver.execute_script("arguments[0].click();", button)

        time.sleep(7)

        print("Update: \"See more jobs\" button clicked.")

def upload_results(new_companies: set):
    """ Take the company names set, convert it to a long sting joined by commas, and upload it to a text file. """
    
    print("Update: Uploading results now")
    
    # Create file if needed
    if not os.path.exists("companies.txt"):
        open("companies.txt", "w").close()
    
    # Read previous fetched list, remove duplicates, and uploaded the updated list
    with open("companies.txt", "r+", encoding="utf-8") as f:
        previous = f.read()
        old_companies = {item.strip() for item in previous.split(",") if item.strip()}
        print(f"Update: Found {len(old_companies)} previously fetched companies.")
        all_companies = old_companies.union(new_companies)
        f.write(", ".join(all_companies))

    print(f"Update: Saved {len(all_companies)} companies to companies.txt")

def find_companies() -> set:
    """ Fetch unique company names from each job that comes up from the greenhouse website search. """

    companies = set()

    print("Update: Fetching company names now.")
    jobs = driver.find_elements(By.CSS_SELECTOR, '[data-provides="search-result"]')

    for job in jobs:
        for p in job.find_elements(By.CSS_SELECTOR, 'p.body'):
            returned_line = p.text
            if "Posted" not in returned_line: # Filter irrelevant responces
                companies.add(returned_line)
    
    upload_results(companies)

def main():
    load_greenhouse()
    load_more_jobs(10)
    find_companies()

if __name__ == "__main__":
    main()

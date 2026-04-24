import random
import time
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

options = Options() 
options.debugger_address = "127.0.0.1:9222"
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

def load_greenhouse():
    driver.get("https://my.greenhouse.io/jobs?query=software%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote")
    time.sleep(2)
    print("Update: Session loaded successfully")

def load_more_jobs(total_page_expansions: int):
    """ Click the button on the bottom of the page to see more jobs as many times as specified by the function arg. """

    try:
        for expansion_number in range(total_page_expansions):
            button = WebDriverWait(driver, 15).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[.//span[text()='See more jobs']]")
                )
            )

            driver.execute_script("arguments[0].click();", button)

            time.sleep(random.randint(2, 7))

            print(f"\rUpdate: \"See more jobs\" button clicked {expansion_number + 1} times.", end = "", flush=True)
    except TimeoutException:
        if driver.find_elements(By.XPATH,"//button[.//span[text()='See more jobs']]"):
            print(f"Update: Loaded the last page, number {expansion_number + 1}.")
        else:
            print(f"Update: Not able to expand any more job pages after going through {expansion_number+1} pages. The button was found but not clickable.") 

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

def extract_token(url: str):
    """ Find open job button url and extract the job token board name exactly as used in the url. """

    match = re.search(r"job-boards\.greenhouse\.io/([^/]+)/jobs", url)
    if match:
        return match.group(1).lower()
    
    return None

def find_companies() -> set:
    """ Fetch unique company names from each job that comes up from the greenhouse website search. """

    companies = set()

    print("Update: Fetching company names now.")
    jobs = driver.find_elements(By.CSS_SELECTOR, '[data-provides="search-result"]')

    for job in jobs:
        btn = job.find_element(
            By.CSS_SELECTOR,
            "a.btn.btn--rounded[rel='noopener noreferrer']"
        )

        link = btn.get_attribute("href")
        company = extract_token(link)
        if company:
            companies.add(company)
    
    upload_results(companies)

def main():
    load_greenhouse()
    load_more_jobs(100)
    find_companies()

if __name__ == "__main__":
    main()

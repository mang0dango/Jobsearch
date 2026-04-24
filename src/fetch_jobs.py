import random
import time
import csv
import os
import re

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

import config

options = Options() 
options.debugger_address = "127.0.0.1:9222"
service = Service("/usr/local/bin/chromedriver")
driver = webdriver.Chrome(service=service, options=options)

def load_greenhouse(query: str):
    """ Load the greenhouse.io search url with the website's search parameters set. """

    driver.get(query)
    time.sleep(2)
    print("Update: Greenhouse session loaded successfully")

def load_more_jobs(total_page_expansions: int):
    """ Click the button on the bottom of the page to see more jobs as many times as specified by the function arg. """

    if total_page_expansions < 0:
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

def upload_results(new_job_links: set, file_path: str = config.UNFILTERED_JOBS):
    """Store unique job URLs in a CSV file, one URL per row."""

    print("Update: Uploading results now")

    # Ensure file exists
    if not os.path.exists(file_path):
        open(file_path, "w", newline="", encoding="utf-8").close()

    # Read existing URLs
    old_jobs = set()
    with open(file_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row in reader:
            if row:  # avoid empty rows
                old_jobs.add(row[0].strip())

    print(f"Update: Found {len(old_jobs)} previously fetched jobs.")

    # Merge with new results
    all_jobs = old_jobs.union(new_job_links)

    # Write back ALL unique URLs (overwrite file cleanly)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        for url in sorted(all_jobs):
            writer.writerow([url])

    print(f"Update: Saved {len(all_jobs)} total unique job URLs.")

def find_jobs() -> set:
    """ Fetch unique job links that come up from the greenhouse website search. """

    new_job_links = set()

    print("Update: Fetching job links now.")
    jobs = driver.find_elements(By.CSS_SELECTOR, '[data-provides="search-result"]')

    for job in jobs:
        btn = job.find_element(
            By.CSS_SELECTOR,
            "a.btn.btn--rounded[rel='noopener noreferrer']"
        )

        link = btn.get_attribute("href")
        if link:
            new_job_links.add(link)
    
    upload_results(new_job_links)

def main():
    for query in config.GREENHOUSE_SEARCHES: 
        try:
            load_greenhouse(query)
            load_more_jobs(config.PAGES_TO_LOAD)
            find_jobs()
        except Exception as e:
            print(e)
            
if __name__ == "__main__":
    main()

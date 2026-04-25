import random
import time
import pandas as pd

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
    """ Load the greenhouse.io search page. """

    driver.get(query)
    time.sleep(3)
    print("Update: Greenhouse session loaded successfully")


def load_more_jobs(total_page_expansions: int = config.PAGES_TO_LOAD):
    """ Expand job listings by clicking 'See more jobs'. """

    if total_page_expansions > 0:
        try:
            for expansion_number in range(total_page_expansions):
                button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[text()='See more jobs']]")
                    )
                )

                driver.execute_script("arguments[0].click();", button)
                time.sleep(random.randint(1, 4))

                print(
                    f"\rUpdate: \"See more jobs\" clicked {expansion_number + 1} times.",
                    end="",
                    flush=True
                )

        except TimeoutException:
            if driver.find_elements(By.XPATH, "//button[.//span[text()='See more jobs']]"):
                print(f"Update: Loaded last page at {expansion_number + 1}.")
            else:
                print("Update: No more pages or button not clickable.")


def find_jobs() -> set:
    """ Scrape job links from current page. """

    new_job_links = set()

    print("Update: Fetching job links now.")

    jobs = driver.find_elements(By.CSS_SELECTOR, '[data-provides="search-result"]')

    for job in jobs:
        try:
            btn = job.find_element(
                By.CSS_SELECTOR,
                "a.btn.btn--rounded[rel='noopener noreferrer']"
            )

            link = btn.get_attribute("href")
            if link:
                new_job_links.add(link)

        except Exception:
            continue

    print(f"Update: Found {len(new_job_links)} jobs in this query.")
    return new_job_links


def save_all_jobs(all_jobs: set, file_path: str = config.UNFILTERED_JOBS):
    """ Upload the final job list to a csv file using pandas (single write). """

    df = pd.DataFrame(sorted(all_jobs), columns=["url"])
    df.to_csv(file_path, index=False)

    print(f"Update: Saved {len(df)} total unique job URLs.")


def main():
    """ Run full scraping pipeline across all queries and save once. """

    all_jobs = set()

    for query in config.GREENHOUSE_SEARCHES:

        try:
            load_greenhouse(query)
            load_more_jobs()
            
            new_jobs = find_jobs()
            print(f"Update: Found {len(new_jobs)} new jobs")
            all_jobs.update(new_jobs)

            print(f"Update: Total collected so far: {len(all_jobs)}")

        except Exception as e:
            print(f"Error on query: {e}")

    print("\nUpdate: Finalizing dataset...")
    save_all_jobs(all_jobs)


if __name__ == "__main__":
    main()

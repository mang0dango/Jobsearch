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

driver = None

def create_driver():
    """Create and return Selenium Chrome driver."""

    options = Options()
    options.debugger_address = "127.0.0.1:9222"
    service = Service("/usr/local/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)

def ensure_greenhouse_logged_in():

    driver.get("https://my.greenhouse.io/jobs")
    time.sleep(2)

    if "sign_in" in driver.current_url:

        yes_values = {"y", "yes"}
        no_values = {"n", "no"}

        while True:
            answer = input(
                "❗ You are not logged in to Greenhouse.\n"
                "Please navigate to greenhouse.io/log_in and enter your details in the new Chrome window.\n"
                "Type Y/Yes when done, or N/No to exit: "
            ).strip().lower()

            if answer in yes_values:
                driver.get("https://my.greenhouse.io/jobs")
                time.sleep(2)

                if "sign_in" not in driver.current_url:
                    print("✔ Login confirmed")
                    return
                else:
                    print("Still not logged in. Try again.")

            elif answer in no_values:
                print("Stopping pipeline.")
                exit(1)

            else:
                print("Invalid input. Please type Y/Yes or N/No.")
    else:
        print("Update: Greenhouse user is signed in, the session can continue.")

def load_greenhouse(query: str):
    """ Load the greenhouse.io search page. """

    driver.get(query)
    time.sleep(3)
    print("Update: Loading new greenhouse search.")


def load_more_jobs(total_page_expansions: int = config.PAGES_TO_LOAD):
    """ Expand job listings by clicking 'See more jobs'. """

    if total_page_expansions > 0:
    
        successful_clicks = 0

        try:
            for expansion_number in range(total_page_expansions):
                breakpoint()
                time.sleep(random.randint(1,5))
                button = WebDriverWait(driver, 15).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[.//span[text()='See more jobs']]")
                    )
                )

                driver.execute_script("arguments[0].click();", button)
                successful_clicks += 1

                print(
                    f"\rUpdate: \"See more jobs\" button clicked {successful_clicks} times.",
                    end="",
                    flush=True
                )

        except TimeoutException:
            print(f"Update: Loaded {successful_clicks + 1} pages.")


def find_jobs() -> set:
    """ Scrape job links from current page. """

    new_job_links = set()

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

    return new_job_links


def save_all_jobs(all_jobs: set, file_path: str = config.UNFILTERED_JOBS):
    """ Upload the final job list to a csv file using pandas (single write). """

    df = pd.DataFrame(sorted(all_jobs), columns=["url"])
    df.to_csv(file_path, index=False)

    print(f"Update: Saved {len(df)} total unique job URLs.")


def main():
    """ Run full scraping pipeline across all queries and save once. """

    global driver
    driver = create_driver()
    ensure_greenhouse_logged_in()
    all_jobs = set()

    for query in config.GREENHOUSE_SEARCHES:

        try:
            load_greenhouse(query)
            load_more_jobs()
            
            page_jobs = find_jobs()
            delta_jobs = page_jobs - all_jobs
            all_jobs.update(delta_jobs)
            print(f"Number of Jobs Found: {len(page_jobs)} | Unique Jobs Found: {len(delta_jobs)} | New Total: {len(all_jobs)}")

        except Exception as e:
            print(f"Error on query: {e}")

    print("\nUpdate: Finalizing dataset...")
    save_all_jobs(all_jobs)


if __name__ == "__main__":
    main()

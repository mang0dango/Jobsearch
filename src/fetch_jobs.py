import random
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
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
    """Ensure user is logged into Greenhouse before scraping."""

    driver.get("https://my.greenhouse.io/jobs")
    time.sleep(2)

    if "sign_in" in driver.current_url:

        yes_values = {"y", "yes"}
        no_values = {"n", "no"}

        while True:

            answer = input(
                "\n❗ You are not logged in to Greenhouse.\n"
                "Please log in using the Chrome window.\n"
                "Type Y/Yes when finished or N/No to exit: "
            ).strip().lower()

            if answer in yes_values:

                driver.get("https://my.greenhouse.io/jobs")
                time.sleep(2)

                if "sign_in" not in driver.current_url:
                    print("✔ Login confirmed")
                    return

                print("Still not logged in. Try again.")

            elif answer in no_values:
                print("Stopping pipeline.")
                exit(1)

            else:
                print("Invalid input.")

    else:
        print("Update: Greenhouse user is signed in.")


def load_greenhouse(query: str):
    """Load a Greenhouse search page."""

    driver.get(query)

    time.sleep(3)

    print("Update: Loading new greenhouse search.")


def scroll_page():
    """Scroll to bottom of current page."""

    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(random.randint(2, 4))


def click_load_more_button():
    """Click 'See more jobs' button if it exists."""

    buttons = driver.find_elements(
        By.XPATH,
        "//button[.//span[text()='See more jobs']]"
    )

    if not buttons:
        return False

    try:

        button = buttons[0]

        # Scroll button into view
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});",
            button
        )

        time.sleep(1)

        # Click button
        driver.execute_script(
            "arguments[0].click();",
            button
        )

        print("Update: Clicked 'See more jobs' button.")

        time.sleep(random.randint(2, 5))

        return True

    except Exception as e:

        print(f"Update: Failed to click button: {e}")

        return False


def collect_visible_jobs() -> set:
    """Collect currently visible job links from DOM."""

    collected_jobs = set()

    jobs = driver.find_elements(
        By.CSS_SELECTOR,
        '[data-provides="search-result"]'
    )

    for job in jobs:

        try:

            btn = job.find_element(
                By.CSS_SELECTOR,
                "a.btn.btn--rounded[rel='noopener noreferrer']"
            )

            link = btn.get_attribute("href")

            if link:
                collected_jobs.add(link)

        except Exception:
            continue

    return collected_jobs

def collect_jobs(max_jobs: int = config.MAX_JOB_COUNT_PER_QUERY) -> set:
""" This functon scrolls the job listings page to account for lazy page loading, collects rendered jobs, clicks load next page button when needed, and rate limits the amount of jobs scraped. """

    collected = set()
    stagnant = 0
    prev_size = 0

    while len(collected) < max_jobs and stagnant < 3:

        scroll_page()
        click_load_more_button()

        collected.update(collect_visible_jobs())

        new_size = len(collected)

        print(f"Collected: {new_size}")

        stagnant = stagnant + 1 if new_size == prev_size else 0
        prev_size = new_size

    return set(list(collected)[:max_jobs])

def save_all_jobs(all_jobs: set, file_path: str = config.UNFILTERED_JOBS):
    """Save all collected jobs to CSV."""

    df = pd.DataFrame(sorted(all_jobs),columns=["url"])

    df.to_csv(file_path, index=False)

    print(f"Update: Saved {len(df)} total unique job URLs.")


def main():
    """Run the job scraping with selenium."""

    global driver

    driver = create_driver()

    ensure_greenhouse_logged_in()

    all_jobs = set()

    for query in config.GREENHOUSE_SEARCHES:

        try:

            load_greenhouse(query)

            page_jobs = collect_jobs()

            new_jobs = page_jobs - all_jobs

            all_jobs.update(new_jobs)

            print(
                f"Query Jobs: {len(page_jobs)} | "
                f"New Unique Jobs: {len(new_jobs)} | "
                f"Total Dataset Size: {len(all_jobs)}"
            )

        except Exception as e:

            print(f"Error on query: {e}")

    print("\nUpdate: Finalizing dataset...")

    save_all_jobs(all_jobs)


if __name__ == "__main__":
    main()

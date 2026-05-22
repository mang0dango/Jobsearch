import random
import time
import pandas as pd

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

import config

driver = None


# ─── DRIVER SETUP ────────────────────────────────────────────────────────────

def create_driver():
    """Create and return Selenium Chrome driver."""

    options = Options()
    options.debugger_address = "127.0.0.1:9222"

    service = Service("/usr/local/bin/chromedriver")

    return webdriver.Chrome(service=service, options=options)


# ─── LOGIN CHECK ─────────────────────────────────────────────────────────────

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


# ─── LOAD SEARCH PAGE ────────────────────────────────────────────────────────

def load_greenhouse(query: str):
    """Load a Greenhouse search page."""

    driver.get(query)

    time.sleep(3)

    print("Update: Loading new greenhouse search.")


# ─── SCROLL PAGE ─────────────────────────────────────────────────────────────

def scroll_page():
    """Scroll to bottom of current page."""

    driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);"
    )

    time.sleep(random.randint(2, 4))


# ─── CLICK LOAD MORE BUTTON ──────────────────────────────────────────────────

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


# ─── COLLECT CURRENTLY RENDERED JOBS ────────────────────────────────────────

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


# ─── MAIN COLLECTION ENGINE ──────────────────────────────────────────────────

def collect_jobs(
    max_jobs: int = config.MAX_JOB_COUNT_PER_QUERY
) -> set:
    """
    Continuously:
    - scroll page
    - collect rendered jobs
    - click load-more button when available

    Stops when:
    - enough jobs collected
    - OR page stops changing
    """

    collected_jobs = set()

    previous_job_count = 0
    stagnant_rounds = 0

    while len(collected_jobs) < max_jobs:

        # Scroll page to trigger lazy rendering
        scroll_page()

        # Collect newly rendered jobs
        visible_jobs = collect_visible_jobs()

        collected_jobs.update(visible_jobs)

        print(
            f"Update: {len(collected_jobs)} unique jobs collected."
        )

        # Stop immediately once limit reached
        if len(collected_jobs) >= max_jobs:

            print(
                f"Update: Reached limit of {max_jobs} jobs."
            )

            break

        # Attempt to click expansion button
        click_load_more_button()

        # Detect if page stopped changing
        current_job_count = len(collected_jobs)

        if current_job_count == previous_job_count:
            stagnant_rounds += 1
        else:
            stagnant_rounds = 0

        previous_job_count = current_job_count

        # Stop after repeated stagnant rounds
        if stagnant_rounds >= 3:

            print(
                "Update: No additional jobs detected."
            )

            break

    return set(list(collected_jobs)[:max_jobs])


# ─── SAVE FINAL JOB DATASET ──────────────────────────────────────────────────

def save_all_jobs(
    all_jobs: set,
    file_path: str = config.UNFILTERED_JOBS
):
    """Save all collected jobs to CSV."""

    df = pd.DataFrame(
        sorted(all_jobs),
        columns=["url"]
    )

    df.to_csv(file_path, index=False)

    print(
        f"Update: Saved {len(df)} total unique job URLs."
    )


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────────

def main():
    """Run full scraping pipeline."""

    global driver

    driver = create_driver()

    ensure_greenhouse_logged_in()

    all_jobs = set()

    for query in config.GREENHOUSE_SEARCHES:

        try:

            # Load search query
            load_greenhouse(query)

            # Collect jobs for this query
            page_jobs = collect_jobs()

            # Track unique additions
            new_jobs = page_jobs - all_jobs

            # Merge into global dataset
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

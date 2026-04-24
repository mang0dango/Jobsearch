import pandas as pd
import time
import requests
from bs4 import BeautifulSoup

import config


def fetch_content(url):
    """ Fetch job title and full page text from job listing. """

    try:
        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        title = soup.find("h1")
        title = title.get_text(strip=True).lower() if title else ""

        text = soup.get_text(separator=" ").lower()

        return title, text
    except Exception:
        return "", ""

def has_blacklist(text):
    """ Check if any blacklist keyword exists in job text. """

    text = f" {text} "

    for word in config.BLACKLIST_KEYWORDS:
        if f" {word} " in text:
            return word

    return None

def skill_score(text):
    """ Count how many skills match in job description. """

    matches = {s for s in config.SKILL_KEYWORDS if s in text}
    return len(matches), matches


def is_us(text):
    """ Determine if job is likely US-based. """

    return any(state.lower() in text for state in config.US_STATES)


def get_company(url):
    """ Extract company name from Greenhouse job URL. """

    parts = url.split("/")
    return parts[3] if len(parts) > 3 else "unknown"


def get_location(text):
    """ Extract US state from job text if present. """

    for state in config.US_STATES:
        if state.lower() in text:
            return state
    return "unknown"


def load_jobs(path):
    """ Load job URLs from CSV safely. """

    try:
        return pd.read_csv(path, header=None, names=["url"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["url"])


def upload(path, rows):
    """ Append processed rows into CSV output file. """

    if not rows:
        return

    df = pd.DataFrame(rows)

    try:
        existing = pd.read_csv(path)
        df = pd.concat([existing, df], ignore_index=True)
    except FileNotFoundError:
        pass

    df.to_csv(path, index=False)


def classify(url):
    """ Classify a job as approved or rejected with metadata. """

    title, text = fetch_content(url)
    combined = f"{title} {text}"

    company = get_company(url)
    location = get_location(combined)
    score, skills = skill_score(combined)

    if not is_us(combined):
        return {
            "status": "rejected",
            "reason": "non-us location",
            "skills_matched": score,
            "company": company,
            "url": url,
            "location": location,
        }

    bad = has_blacklist(combined)
    if bad:
        return {
            "status": "rejected",
            "reason": f"blacklist: {bad}",
            "skills_matched": score,
            "company": company,
            "url": url,
            "location": location,
        }

    if score >= config.MIN_NUMBER_OF_SKILLS_MATCHED:
        return {
            "status": "approved",
            "reason": "",
            "skills_matched": score,
            "skills_list": ", ".join(skills),
            "company": company,
            "url": url,
            "location": location,
        }

    return {
        "status": "rejected",
        "reason": f"only {score} skills matched",
        "skills_matched": score,
        "company": company,
        "url": url,
        "location": location,
    }


def filter_jobs():
    """ Check if job has any blacklisted terms, confirm the location, and see if the skills match. """

    approved_count = 0
    rejected_count = 0
    rows = []
    processed_rows = []

    try:
        unfiltered = load_jobs(config.UNFILTERED_JOBS)
        processed = load_jobs(config.PROCESSED_JOBS)
        processed_set = set(processed["url"])
        unfiltered = unfiltered[~unfiltered["url"].isin(processed_set)]
        total = len(unfiltered)
 
        print(f"Update: Starting processing {total} jobs")

        for i, url in enumerate(unfiltered["url"], start=1):
            result = classify(url)

            rows.append(result)
            processed_rows.append({"url": url})

            if result["status"] == "approved":
                approved_count += 1
            else:
                rejected_count += 1

            percent = (i / total) * 100

            print(
                f"\rProcessed {i}/{total} ({percent:.2f}%) | "
                f"Approved: {approved_count} | Rejected: {rejected_count}",
                end="",
                flush=True
            )

            time.sleep(config.REQUEST_DELAY)

    except KeyboardInterrupt:
        print("\nUpdate: Interrupted by user (Ctrl+C)")

    except Exception as e:
        print(e)

    finally:
        if total:
            df = pd.DataFrame(rows)
            
            return df, processed_rows, total
        else:
            print("Update: All fetched jobs have already been processed.")
            quit()

def main():
    """ Run full job filtering pipeline and aupload results """

    df, processed_rows, total = filter_jobs()
    
    approved = df[df["status"] == "approved"].copy()
    rejected = df[df["status"] == "rejected"].copy()
    approved = approved.sort_values(by="skills_matched", ascending=False)
    
    print("Update: Uploading results")
    upload(config.APPROVED_JOBS, approved.to_dict("records"))
    upload(config.REJECTED_JOBS, rejected.to_dict("records"))
    upload(config.PROCESSED_JOBS, processed_rows)
    

if __name__ == "__main__":
    main()

import pandas as pd
import time
import requests
from bs4 import BeautifulSoup

import config

def fetch_content(url):
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
    for word in config.BLACKLIST_KEYWORDS:
        if word in text:
            return word
    return None

def skill_score(text):
    matches = {s for s in config.SKILL_KEYWORDS if s in text}
    return len(matches), matches

def is_us(text):
    return any(state.lower() in text for state in config.US_STATES)

def get_company(url):
    parts = url.split("/")
    return parts[3] if len(parts) > 3 else "unknown"

def get_location(text):
    for state in config.US_STATES:
        if state.lower() in text:
            return state
    return "unknown"

def get_work_mode():
    pass

def load_jobs(path):
    try:
        return pd.read_csv(path, header=None, names=["url"])
    except FileNotFoundError:
        return pd.DataFrame(columns=["url"])

def upload(path, rows):
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

    else:
        return {
            "status": "rejected",
            "reason": f"only {score} skills matched",
            "skills_matched": score,
            "company": company,
            "url": url,
            "location": location,
        }


def main():
    unfiltered = load_jobs(config.UNFILTERED_JOBS)
    processed = load_jobs(config.PROCESSED_JOBS)

    processed_set = set(processed["url"])

    unfiltered = unfiltered[~unfiltered["url"].isin(processed_set)]

    rows = []
    processed_rows = []

    for url in unfiltered["url"]:
        result = classify(url)

        rows.append(result)
        processed_rows.append({"url": url})

        time.sleep(config.REQUEST_DELAY)

    df = pd.DataFrame(rows)

    approved = df[df["status"] == "approved"].copy()
    rejected = df[df["status"] == "rejected"].copy()

    approved = approved.sort_values(by="skills_matched", ascending=False)

    upload(config.APPROVED_JOBS, approved.to_dict("records"))
    upload(config.REJECTED_JOBS, rejected.to_dict("records"))
    upload(config.PROCESSED_JOBS, processed_rows)


if __name__ == "__main__":
    main()

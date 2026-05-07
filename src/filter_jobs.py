import pandas as pd
import time
import requests
import re
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


def has_experience_blacklist(text):
    """ Check experience blacklist with contextual override logic. """

    text_lower = text.lower()

    for word in config.BLACKLIST_EXPERIENCE_KEYWORDS:

        for match in re.finditer(rf"\b{re.escape(word)}\b", text_lower):

            start = max(0, match.start() - 100)
            end = min(len(text_lower), match.end() + 100)

            window = text_lower[start:end]

            # If collaborative context exists near keyword → ignore
            if any(ctx in window for ctx in config.COLLABORATIVE_KEYWORDS):
                continue

            return word

    return None


def has_skill_blacklist(text):
    """ Check if any skill blacklist keyword exists in job text. """

    text = f" {text} "

    for word in config.BLACKLIST_SKILL_KEYWORDS:
        if f" {word} " in text:
            return word

    return None


def skill_score(text):
    """ Count how many skills match in job description. """

    matches = {s for s in config.SKILL_KEYWORDS if s in text}
    return len(matches), matches



def get_company(url):
    """ Extract company name from Greenhouse job URL. """

    parts = url.split("/")
    return parts[3] if len(parts) > 3 else "unknown"


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
        df = df.drop_duplicates(subset=["url"])
        if "skills_matched" in df.columns:
            df = df.sort_values(by="skills_matched", ascending=False)
    except FileNotFoundError:
        pass

    df.to_csv(path, index=False)


def classify(url):
    """ Classify a job as approved or rejected with metadata. """

    date = datetime.now().strftime("%d/%m/%Y")
    title, text = fetch_content(url)
    combined = f"{title} {text}"

    company = get_company(url)
    score, skills = skill_score(combined)

    bad_exp = has_experience_blacklist(combined)
    if bad_exp:
        return {
            "date_found": date,
            "application_status": "",
            "date_applied": "",
            "company": company,
            "url": url,
            "reason": f"experience blacklist: {bad_exp}",
            "skills_matched": score,
            "status": "rejected",
        }

    bad_skill = has_skill_blacklist(combined)
    if bad_skill:
        return {
            "date_found": date,
            "application_status": "",
            "date_applied": "",
            "company": company,
            "url": url, 
            "reason": f"skill blacklist: {bad_skill}",
            "skills_matched": score,
            "status": "rejected",
        }

    if score >= config.MIN_NUMBER_OF_SKILLS_MATCHED:
        return {
            "date_found": date,
            "application_status": "",
            "date_applied": "",
            "company": company,
            "url": url,
            "skills_matched": score,
            "skills_list": ",".join(skills),
            "status": "approved",
        }

    return {
        "date_found": date,
        "application_status": "",
        "date_applied": "",
        "company": company,
        "url": url,
        "reason": f"only {score} skills matched",
        "skills_matched": score,
        "status": "rejected",
    }


def filter_jobs():
    """ Check if job has any blacklisted terms and see if the skills match. """

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
    """ Run full job filtering pipeline and upload results """

    df, processed_rows, total = filter_jobs()

    approved = df[df["status"] == "approved"].copy()
    rejected = df[df["status"] == "rejected"].copy()
    approved = approved.sort_values(by="skills_matched", ascending=False)

    print("\nUpdate: Uploading results")
    upload(config.APPROVED_JOBS, approved.to_dict("records"))
    upload(config.REJECTED_JOBS, rejected.to_dict("records"))
    upload(config.PROCESSED_JOBS, processed_rows)


if __name__ == "__main__":
    main()

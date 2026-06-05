import pandas as pd
from datetime import datetime
import time
import requests
import re
from bs4 import BeautifulSoup
import csv

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
        return pd.read_csv(path)
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

    except FileNotFoundError:
        pass

    df.to_csv(path, index=False)

def record(unknown_questions: list[str]):
    """ Write the questions which the code could not understand in a separate file to help adjust the text analysis for the future. """
    
    if unknown_questions: 
        with open(config.UNKNOWN_QUESTIONS, 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(unknown_questions)

def fetch_questions(url: str) -> list[str]:
    """ Fetch all the job application form questions. """

    questions = []

    try:

        res = requests.get(url, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        text_q_wrappers = soup.find_all("div", class_="input-wrapper") 
        dropdown_q_wrappers = soup.find_all("div", class_="select__container")
        wrappers = text_q_wrappers + dropdown_q_wrappers

        for wrapper in wrappers:
            label = wrapper.find("label")

            if label:
                question = label.get_text(strip=True)
                if "*" in question: 
                    normalized_q = question.lower().replace("*","")
                    questions.append(normalized_q)
        
        return questions
    except Exception as e:
        print(e)
        return []

def evaluate_difficulty(url: str) -> str:
    """ Check if the job application form has any questions that are not boilerplate questions, such as name, etc.
    If there are more complex customized questions, then evaluate complexity of the questions and overall form based on common key words that denote the nature of the question. 
    For questions that the companies wrote themselves instead of boilerplate questions, the wording might change while referring to the same topic. """ 

    try:
        
        status = "unassigned"
        unknown_questions = []

        questions = fetch_questions(url)
        custom_questions = [q for q in questions if q not in config.BOILERPLATE_QUESTIONS] 

        if custom_questions:
            for q in custom_questions:
                if not any(phrase in q for phrase in config.ALL_KEY_PHRASES):
                    status = "unknown"
                    unknown_questions.append(q)
                elif any(phrase in q for phrase in config.HARD_KEY_PHRASES):
                    if status == "unassigned" or status == "easy" or status == "medium":
                        status = "hard"
                elif any(phrase in q for phrase in config.MEDIUM_KEY_PHRASES):
                    if status == "unassigned" or status == "easy":
                        status = "medium"
                elif any(phrase in q for phrase in config.EASY_KEY_PHRASES):
                    if status == "unassigned":
                        status = "easy"
        elif questions:
            status = "boilerplate"
        
        if unknown_questions:
            record(unknown_questions)

        return status

    except Exception:
        return "unassigned"

def classify(url):
    """ Classify a job as approved or rejected with metadata. """

    date = datetime.now().strftime("%m/%d/%Y")
    title, text = fetch_content(url)
    combined = f"{title} {text}"

    company = get_company(url)
    score, skills = skill_score(combined)

    if "greenhouse.io" not in url:
        return {
            "date_found": date,
            "application_status": "",
            "date_applied": "",
            "company": company,
            "url": url, 
            "reason": "not default greenhouse url",
            "skills_matched": "",
            "status": "unfiltered",
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

    if score >= config.MIN_NUMBER_OF_SKILLS_MATCHED:
        return {
            "date_found": date,
            "application_status": "",
            "date_applied": "",
            "company": company,
            "url": url,
            "questions": evaluate_difficulty(url), 
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
    unfiltered_count = 0
    rows = []
    processed_rows = []
    total = 0  

    try:
        fetched_jobs = load_jobs(config.FETCHED_JOBS)
        processed = load_jobs(config.PROCESSED_JOBS)
        processed_set = set(processed["url"])
        jobs_to_process = fetched_jobs[~fetched_jobs["url"].isin(processed_set)]
        total = len(jobs_to_process)
        
        if total > 0:
            print(f"Update: Starting processing {total} jobs")

            for i, url in enumerate(jobs_to_process["url"], start=1):
                result = classify(url)

                rows.append(result)
                processed_rows.append({"url": url})

                if result["status"] == "approved":
                    approved_count += 1
                elif result["status"] == "rejected":
                    rejected_count += 1
                elif result["status"] == "unfiltered":
                    unfiltered_count += 1

                percent = (i / total) * 100 if total else 0

                print(
                    f"\rProcessed {i}/{total} ({percent:.2f}%) | "
                    f"Approved: {approved_count} | Rejected: {rejected_count} | Unfiltered: {unfiltered_count}",
                    end="",
                    flush=True
                )

                time.sleep(config.REQUEST_DELAY)
            
            df = pd.DataFrame(rows)
            
            return df, processed_rows, total

        else:
            print("Update: no jobs to filter, exiting now.")
            exit()
    except Exception as e:
        print(e)
        return None, [], 0 



def main():
    """ Run the job filtering pipeline, sort, and upload results. """

    df, processed_rows, total = filter_jobs()

    approved_df = df[df["status"] == "approved"]

    approved_df["questions"] = pd.Categorical(
        approved_df["questions"],
        categories=[
            "boilerplate",
            "easy",
            "medium",
            "hard",
            "unknown",
        ],
        ordered=True,
    )

    unfiltered = df[df["status"] == "unfiltered"].sort_values(by="date_found", ascending=False).to_dict("records")
    rejected = df[df["status"] == "rejected"].sort_values(by="date_found", ascending=False).to_dict("records")
    approved = df[df["status"] == "approved"].sort_values(by=["skills_matched", "questions" ,"date_found"], ascending=[False, True, False]).to_dict("records")

    print("\nUpdate: Uploading results")
    upload(config.APPROVED_JOBS, approved)
    upload(config.REJECTED_JOBS, rejected)
    upload(config.UNFILTERED_JOBS, unfiltered)
    upload(config.PROCESSED_JOBS, processed_rows)
        
if __name__ == "__main__":
    main()

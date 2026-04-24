#!/usr/bin/env python3
"""
Greenhouse Job Scraper — Maiia Kishchukova
Tailored for: Python, AWS/GCP, SQL, ML/NLP, Docker, Kubernetes, Airflow, Snowflake
"""

import requests
import csv
import re
import os
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────

MIN_MATCH_SCORE  = 60
MAX_JOBS         = 300
REQUEST_DELAY    = 0.25

APPLIED_CSV      = "applied_to_jobs.csv"
SEEN_FILE        = "seen_jobs.txt"
OUTPUT_CSV       = "new_jobs_to_apply.csv"
REJECTED_CSV     = "rejected_jobs.csv"

# ─── FILTERS ──────────────────────────────────────────────────────────────────

TITLE_KEYWORDS = [
    "machine learning", "ML", "IT Support","engineer", "developer", "software", "backend", "software engineer", "data engineer", "ml engineer",
    "machine learning engineer", "platform engineer", "python engineer",
    "cloud engineer", "devops engineer", "sre", "mlops",
]

HIGH_VALUE_KEYWORDS = [
    "python", "aws", "gcp", "snowflake", "airflow",
    "kubernetes", "machine learning", "nlp",
]

MED_VALUE_KEYWORDS = [
    "docker", "postgresql", "terraform", "linux",
    "ci/cd", "kafka", "spark", "dbt", "ml",
]

EXCLUDE_KEYWORDS = [
    "senior", "staff", "principal", "director", "manager",
    "frontend", "lead", "android", "analyst", "architect", "account executive",
]

REMOTE_INDICATORS = ["remote", "anywhere", "distributed", "wfh"]
US_STATES = ["CA","NY","TX","WA","FL","MA","IL","CO","NC","GA"]
NON_US_INDICATORS = ["london", "berlin", "toronto", "singapore"]

# ─── SEED TOKENS ──────────────────────────────────────────────────────────────

SEED_TOKENS = ["databricks", "snowflake", "stripe", "openai", "figma", "duolingo"]

# ─── CACHE ────────────────────────────────────────────────────────────────────

def load_seen_ids(filepath: str) -> set:
    if not os.path.isfile(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        return {line.strip() for line in f if line.strip()}

def save_seen_ids(filepath: str, new_ids: set):
    with open(filepath, "a", encoding="utf-8") as f:
        for i in new_ids:
            f.write(i + "\n")

# ─── APPLIED URLS ─────────────────────────────────────────────────────────────

def load_applied_urls(filepath: str) -> set:
    urls = set()
    if not os.path.isfile(filepath):
        return urls
    with open(filepath, newline="", encoding="utf-8", errors="ignore") as f:
        for row in csv.reader(f):
            for cell in row:
                if "http" in cell:
                    urls.add(cell.strip().lower())
    return urls

def _norm(u): return u.strip().lower().rstrip("/")

# ─── REJECTED LOG ─────────────────────────────────────────────────────────────

REJECTED_COLS = ["token", "job_link", "is_relevant", "reason", "score"]

def append_rejected(rows: list):
    file_exists = os.path.isfile(REJECTED_CSV)
    with open(REJECTED_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=REJECTED_COLS)
        if not file_exists:
            w.writeheader()
        w.writerows(rows)

# ─── FETCH ────────────────────────────────────────────────────────────────────

def fetch_jobs(token: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    try:
        r = requests.get(url, timeout=10)
        return r.json().get("jobs", []) if r.status_code == 200 else []
    except:
        return []

def build_url(job, token):
    return f"https://job-boards.greenhouse.io/{token}/jobs/{job.get('id','')}"

# ─── SCORING ──────────────────────────────────────────────────────────────────

def score_job(job):
    text = (job.get("title","") + job.get("content","")).lower()
    return min(
        sum(10 for k in HIGH_VALUE_KEYWORDS if k in text) +
        sum(5 for k in MED_VALUE_KEYWORDS if k in text),
        100
    )

def is_relevant(job):
    title = (job.get("title") or "").lower()
    content = (job.get("content") or "").lower()
    location = " ".join(o.get("name","") for o in job.get("offices", [])).lower()

    if not any(k in title for k in TITLE_KEYWORDS):
        return False, "title_mismatch"

    for ex in EXCLUDE_KEYWORDS:
        if ex in title or ex in content:
            return False, f"excluded:{ex}"

    if location:
        if any(x in location for x in NON_US_INDICATORS):
            return False, "non_us"

    return True, "ok"

# ─── COMPANIES ────────────────────────────────────────────────────────────────

def fetch_all_gh_companies():
    tokens = set(SEED_TOKENS)
    return tokens

# ─── OUTPUT ───────────────────────────────────────────────────────────────────

OUTPUT_COLS = ["Date Applied","Company","Job Title","Link","My Follow Up","Status","Extra"]

def append_output(rows):
    file_exists = os.path.isfile(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        if not file_exists:
            w.writeheader()
        w.writerows(rows)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    seen = load_seen_ids(SEEN_FILE)
    applied = load_applied_urls(APPLIED_CSV)

    results = []
    rejected = []
    new_seen = set()

    companies = fetch_all_gh_companies()

    for token in companies:
        jobs = fetch_jobs(token)
        if not jobs:
            continue

        for job in jobs:
            job_id = str(job.get("id"))

            if job_id in seen:
                continue
            new_seen.add(job_id)

            url = build_url(job, token)
            score = score_job(job)
            ok, reason = is_relevant(job)

            if not ok:
                rejected.append({
                    "token": token,
                    "job_link": url,
                    "is_relevant": "no",
                    "reason": reason,
                    "score": score
                })
                continue

            if score < MIN_MATCH_SCORE:
                rejected.append({
                    "token": token,
                    "job_link": url,
                    "is_relevant": "no",
                    "reason": "low_score",
                    "score": score
                })
                continue

            results.append({
                "Date Applied": "",
                "Company": token,
                "Job Title": job.get("title",""),
                "Link": url,
                "My Follow Up": "",
                "Status": "",
                "Extra": f"Score:{score}"
            })

        time.sleep(REQUEST_DELAY)

    append_output(results)
    append_rejected(rejected)
    save_seen_ids(SEEN_FILE, new_seen)

    print(f"Done. {len(results)} matched, {len(rejected)} rejected.")

if __name__ == "__main__":
    main()

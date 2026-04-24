import requests
import csv
from urllib.parse import urlparse

# ---------------------------
# INPUT: paste your Google result links here
# ---------------------------
links = [
    "https://boards.greenhouse.io/stripe/jobs/12345",
    "https://boards.greenhouse.io/airbnb/jobs/67890",
    # add ~300 links here
]

# ---------------------------
# STEP 1: extract board tokens
# ---------------------------
def extract_board_token(url: str):
    try:
        print(url)
        path_parts = urlparse(url).path.strip("/").split("/")
        return path_parts[0] if path_parts else None
    except:
        return None

tokens = list({
    extract_board_token(link)
    for link in links
    if extract_board_token(link)
})

print(f"Found {len(tokens)} unique companies")

# ---------------------------
# STEP 2: fetch jobs
# ---------------------------
def fetch_jobs(board_token: str):
    url = f"https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs?content=true"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            return res.json().get("jobs", [])
    except:
        pass
    return []

all_jobs = []
for token in tokens:
    jobs = fetch_jobs(token)
    all_jobs.extend(jobs)

print(f"Fetched {len(all_jobs)} total jobs")

# ---------------------------
# STEP 3: filter jobs
# ---------------------------
include = ["software engineer", "backend", "python", "machine learning", "software developer"]
exclude = ["senior", "staff", "principal", "full stack", "full-stack", "engineer III", "engineer IV", "engineer V", "associate", "lead", "5 year", "5+ year", "6+ year", "6 year", "8 year", "india", "tokyo", "brazil", "mexico", "germany", "korea"]

def is_match(job):
    text = (
        job.get("title", "") + " " +
        job.get("location", {}).get("name", "") + " " +
        job.get("company_name", "")
    ).lower()
    
    print(text)

    return (
        any(word in text for word in include)
        and not any(word in text for word in exclude)
    )

filtered_jobs = [job for job in all_jobs if is_match(job)]

print(f"{len(filtered_jobs)} jobs after filtering")

# ---------------------------
# STEP 4: deduplicate jobs
# ---------------------------
seen = set()
unique_jobs = []

for job in filtered_jobs:
    if job["id"] not in seen:
        seen.add(job["id"])
        unique_jobs.append(job)

print(f"{len(unique_jobs)} unique jobs")

# ---------------------------
# STEP 5: export to CSV
# ---------------------------
with open("greenhouse_jobs.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    
    # header
    writer.writerow([
        "Company",
        "Title",
        "Location",
        "URL"
    ])
    
    for job in unique_jobs:
        writer.writerow([
            job.get("company_name", ""),
            job.get("title", ""),
            job.get("location", {}).get("name", ""),
            job.get("absolute_url", "")
        ])

print("✅ Exported to greenhouse_jobs.csv")

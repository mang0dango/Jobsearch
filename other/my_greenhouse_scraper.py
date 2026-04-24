#!/usr/bin/env python3

"""
Greenhouse Job Scraper — Maiia Kishchukova
Tailored for: Python, AWS/GCP, SQL, ML/NLP, Docker, Kubernetes, Airflow, Snowflake

SETUP:
    pip install requests
    pip install pandas

USAGE:
    python greenhouse_scraper.py

FILES (all in same folder as script):
    applied_to_jobs.csv     — your existing spreadsheet; URLs here are skipped
    seen_jobs.txt           — auto-created; stores IDs of every job ever looked at
                              so re-runs skip them instantly without re-scoring
    new_jobs_to_apply.csv   — output; new rows are appended, never overwritten

HOW IT WORKS:
    1. Discovers ALL companies on Greenhouse via their public board index
    2. For each company, fetches open jobs
    3. Skips instantly if job ID is in seen_jobs.txt (already processed)
    4. Skips if URL is in applied_to_jobs.csv (already applied)
    5. Applies title/exclusion/location filters
    6. Scores against your stack — only jobs scoring >= 60 make the output
    7. Writes matched jobs to new_jobs_to_apply.csv (appended)
    8. Marks ALL seen job IDs (matched or not) in seen_jobs.txt
"""

import requests
import pandas as pd
from typing import List, Union
import csv
import re
import os
import time

# ─── CONFIG ───────────────────────────────────────────────────────────────────

MIN_MATCH_SCORE  = 60        # Jobs below this score are skipped
MAX_JOBS         = 300       # Keep going until this many qualified matches found
REQUEST_DELAY    = 0.25      # Seconds between API calls

APPLIED_CSV      = "applied_to_jobs.csv"   # Your existing applied-jobs sheet
SEEN_FILE        = "seen_jobs.csv"          # Cache of all processed job IDs
OUTPUT_CSV       = "new_jobs_to_apply.csv"  # Results file (append mode)

# ─── FILTERS ──────────────────────────────────────────────────────────────────

TITLE_KEYWORDS = [
    "backend", "back-end", "back end",
    "software engineer", "software developer",
    "data engineer", "ml engineer",
    "machine learning engineer", "platform engineer",
    "python engineer", "cloud engineer",
    "devops engineer", "site reliability", "sre",
    "ai engineer", "mlops",
]

HIGH_VALUE_KEYWORDS = [
    "python", "aws", "gcp", "snowflake", "airflow",
    "data engineer", "machine learning", "nlp", "kubernetes",
]
MED_VALUE_KEYWORDS = [
    "docker", "postgresql", "dynamodb", "terraform", "bash",
    "linux", "rest api", "ci/cd", "gitlab", "backend",
    "data pipeline", "kafka", "spark", "dbt", "ml",
]

EXCLUDE_KEYWORDS = [
    # Internships
    "intern", "internship", "co-op", "coop", "co op",
    # Over-leveled
    "senior", "sr.", "sr ", "lead engineer", "lead developer",
    "staff engineer", "staff developer", "staff software",
    "principal engineer", "principal developer", "principal software",
    "founding engineer", "founding developer", "founding software",
    "distinguished engineer",
    # Level numbers (III+ = 5+ YOE at most companies)
    "engineer iii", "engineer iv", "engineer v",
    "level 5", "level 6", "l5", "l6",
    "engineer 3", "engineer 4", "engineer 5",
    "swe iii", "swe iv", "swe 3", "swe 4",
    # Management
    "director", "vp ", "vice president", "head of", "manager",
    "engineering manager", "tech lead", "technical lead",
    # Years of experience (5+)
    "5+ years", "6+ years", "7+ years", "8+ years", "9+ years", "10+ years",
    "5 years of experience", "6 years of experience",
    "7 years of experience", "8 years of experience",
    "minimum 5 years", "at least 5 years",
    # Unrelated stacks
    "frontend", "front-end", "ios developer", "android developer",
    "mobile engineer", "ruby on rails", ".net developer", "php developer",
    "salesforce", "embedded systems", "firmware", "c++ engineer",
]

REMOTE_INDICATORS = ["remote", "anywhere", "distributed", "work from home", "wfh"]
NON_US_INDICATORS = [
    "london", "berlin", "amsterdam", "toronto", "sydney", "singapore",
    "dubai", " india", "uk only", "canada only", "australia", "germany",
    "france", "netherlands", "brazil", "mexico city", "warsaw", "prague",
]

# ─── SEEN JOBS CACHE ──────────────────────────────────────────────────────────

def load_seen_ids(filepath:str) -> list[Union[int,set[int]]]:
    if not os.path.isfile(filepath):
        return [0, set()]
    else:
        df = pd.read_csv("file.csv")
            row_count = len(df)
"
def load_seen_ids(filepath: str) -> set:
    """Load all previously processed job IDs from cache file."""
    
    if not os.path.isfile(filepath):
        return set()
    with open(filepath, "r", encoding="utf-8") as f:
        ids = {line.strip() for line in f if line.strip()}
    print(f"Cache:   {len(ids):>6} previously seen job IDs loaded from {filepath}")
    return ids


def save_seen_ids(filepath: str, new_ids: set):
    """Append newly seen job IDs to cache file."""
    
    with open(filepath, "a", encoding="utf-8") as f:
        for job_id in sorted(new_ids):
            f.write(f"{job_id}\n")


# ─── APPLIED URLS ─────────────────────────────────────────────────────────────

def load_applied_urls(*filepaths) -> set:
    """
    Read one or more CSV files and extract every URL found in any cell.
    Tries multiple encodings to handle Google Sheets exports.
    """
    urls = set()
    url_re = re.compile(r'https?://[^\s,\"\'<>\r\n]+')

    for filepath in filepaths:
        if not os.path.isfile(filepath):
            if filepath == APPLIED_CSV:
                print(f"Warning: '{filepath}' not found — no deduplication against applied jobs.")
            continue
        loaded = False
        for encoding in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
            try:
                with open(filepath, newline="", encoding=encoding) as f:
                    for row in csv.reader(f):
                        for cell in row:
                            for url in url_re.findall(cell):
                                urls.add(_norm(url))
                print(f"Applied: {len(urls):>6} URLs loaded from {filepath} (encoding: {encoding})")
                loaded = True
                break
            except UnicodeDecodeError:
                continue
        if not loaded:
            # Absolute fallback
            with open(filepath, newline="", encoding="utf-8", errors="replace") as f:
                for row in csv.reader(f):
                    for cell in row:
                        for url in url_re.findall(cell):
                            urls.add(_norm(url))
            print(f"Applied: {len(urls):>6} URLs loaded from {filepath} (fallback encoding)")

    return urls


def _norm(url: str) -> str:
    return url.strip().rstrip("/").lower()


# ─── GREENHOUSE DISCOVERY ─────────────────────────────────────────────────────

# Large seed list of known Greenhouse customers — used as fallback and supplement.
# Greenhouse has no public "list all companies" API; the sitemap is the best
# discovery mechanism. This list covers tech, fintech, data, AI, and infra companies.
SEED_TOKENS = [
    # Data / Analytics / Pipelines
    "databricks", "snowflake", "fivetran", "airbyte", "dbt",
    "prefect", "dagster", "astronomer", "montecarlodata",
    "segment", "rudderstack", "amplitude", "mixpanel", "heap",
    "census", "hightouch", "cube", "lightdash", "metabase", "preset",
    "dremio", "starburst", "rockset", "imply", "clickhouse",
    "feast", "tecton", "hopsworks", "soda", "datafold",
    "atlan", "secoda", "metaphor", "selectstar",
    # Cloud / Infra / DevOps
    "hashicorp", "cloudflare", "fastly", "render", "vercel", "netlify",
    "turbot", "env0", "spacelift", "atlantis",
    "chronosphere", "grafana", "honeycomb", "pagerduty", "incident",
    "opstrace", "groundcover", "komodor", "loft",
    "pulumi", "crossplane", "porter",
    # AI / ML / LLM
    "anthropic", "cohere", "modal", "together", "scale", "huggingface",
    "weights", "labelbox", "roboflow", "activeloop",
    "qdrant", "weaviate", "pinecone",
    "arize", "whylabs", "evidently", "fiddler",
    "verta", "bentoml", "mystic",
    "baseten", "lepton", "fireworks",
    "langchain", "llamaindex", "guardrailsai",
    # Fintech / Payments
    "stripe", "plaid", "moderntreasury", "brex", "ramp", "mercury",
    "coinbase", "chainalysis", "stytch", "lithic",
    "robinhood", "chime", "nubank", "unit",
    "synapse", "increase", "column", "treasury-prime",
    "samsara", "marqeta", "adyen",
    # Backend SaaS / Developer Tools
    "twilio", "sendgrid", "postman", "readme",
    "cockroachdb", "planetscale", "supabase", "neon", "turso",
    "temporal", "replit", "gitlab", "sourcegraph", "retool", "appsmith",
    "gitpod", "codeium", "tabnine", "pieces",
    "mux", "livekit", "daily", "agora",
    "ngrok", "hookdeck", "svix",
    # Security / Compliance
    "lacework", "orca", "wiz", "snyk", "chainguard",
    "drata", "vanta", "secureframe", "anecdotes",
    "semgrep", "endorlabs", "socket",
    # Consumer / Marketplace
    "airbnb", "doordash", "instacart", "gopuff", "shipbob",
    "faire", "klaviyo", "attentive", "postscript",
    "tubi", "discord", "duolingo", "coursera",
    "navan", "tripadvisor",
    # HR / People Ops
    "lattice", "rippling", "gusto", "deel", "remote",
    "hibob", "leapsome", "culture-amp",
    # Productivity
    "figma", "notion", "linear", "loom", "miro",
    # Healthcare / BioTech
    "benchling", "tempus", "flatiron", "komodohealth",
    "medallion", "ribbon", "cedar", "collectivehealth",
    # Logistics / Hardware
    "verkada", "samsara", "anduril", "joby",
    # More known Greenhouse users
    "fanaticsfbg", "angi", "ethoslife",
    "torcrobotics", "boxcast", "tigergraph", "life360",
    "cadencesolutions", "verse", "defenseunicorns",
    "datadog", "confluent", "elastic", "mongodb",
    "okta", "auth0",
    "pagerduty", "opsgenie",
    "conductor", "camunda",
    "immuta", "privacera",
    "plex", "twitch", "masterclass",
    "brainly", "edx", "udemy",
    "seatgeek", "stubhub", "gametime",
    "workato", "zapier", "tray",
    "census", "polytomic", "grouparoo",
    "stedi", "orderful",
    "launchdarkly", "split", "optimizely",
    "algolia", "typesense", "meilisearch",
    "contentful", "sanity", "prismic",
    "expensify", "brex", "fyle", "ramp",
    "lendio", "greenlight", "acorns",
    "gemini", "kraken", "anchorage",
    "openai", "mistral", "aleph-alpha",
    "perplexity", "you", "kagi",
    "mendable", "trulens", "promptlayer",
    "replicate", "banana", "cerebrium",
    "deepgram", "assemblyai", "rev",
    "typeface", "jasper", "copy-ai",
    "runway", "pika", "stability",
    "comet", "neptune", "wandb",
    "mlflow", "clearml", "polyaxon",
    "pachyderm", "dvc", "zenml",
    "superwise", "aporia", "nannyml",
    "truera", "fiddler", "arthur",
]


def fetch_all_gh_companies() -> list:
    """
    Build the list of Greenhouse board tokens to scan.

    Strategy (in order):
    1. Try to fetch boards.greenhouse.io/sitemap.xml — Greenhouse publishes a
       sitemap that contains URLs for every public job board, e.g.:
         <loc>https://boards.greenhouse.io/acmeinc</loc>
       Parsing this gives us thousands of real, active board slugs.
    2. Try the sitemap index first (sitemap_index.xml) which may link to
       multiple sub-sitemaps.
    3. Always add SEED_TOKENS as supplement / fallback so the script
       works even if the sitemap is blocked.
    """
    seen   = set()
    tokens = []

    def add(slug: str):
        slug = slug.strip().lower()
        # Skip Greenhouse infrastructure paths and very short slugs
        if slug and slug not in seen and slug not in {
            "embed", "api", "js", "css", "static", "assets",
            "favicon", "robots", "sitemap", "images", "fonts",
        } and len(slug) > 2:
            seen.add(slug)
            tokens.append(slug)

    # ── Step 1: Try sitemap index ──────────────────────────────────────────
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0"}
    sitemap_urls_to_try = [
        "https://boards.greenhouse.io/sitemap.xml",
        "https://boards.greenhouse.io/sitemap_index.xml",
        "https://job-boards.greenhouse.io/sitemap.xml",
    ]

    for sitemap_url in sitemap_urls_to_try:
        try:
            print(f"Fetching sitemap: {sitemap_url} ...", end=" ", flush=True)
            resp = requests.get(sitemap_url, timeout=20, headers=headers)
            if resp.status_code != 200:
                print(f"HTTP {resp.status_code}, skipping.")
                continue

            xml = resp.text

            # Check if this is a sitemap index (links to sub-sitemaps)
            sub_sitemaps = re.findall(r'<loc>(https://[^<]+sitemap[^<]+)</loc>', xml)
            if sub_sitemaps:
                print(f"index with {len(sub_sitemaps)} sub-sitemaps, fetching...")
                for sub_url in sub_sitemaps[:20]:  # cap at 20 sub-sitemaps
                    try:
                        sub = requests.get(sub_url, timeout=15, headers=headers)
                        if sub.status_code == 200:
                            for slug in re.findall(
                                r'https://(?:boards|job-boards)\.greenhouse\.io/([a-z0-9_-]+)',
                                sub.text
                            ):
                                add(slug)
                    except Exception:
                        continue
                    time.sleep(0.2)
            else:
                # Direct sitemap — extract slugs
                for slug in re.findall(
                    r'https://(?:boards|job-boards)\.greenhouse\.io/([a-z0-9_-]+)',
                    xml
                ):
                    add(slug)

            if tokens:
                print(f"found {len(tokens)} board tokens.")
                break
            else:
                print("no tokens found.")

        except Exception as e:
            print(f"error: {e}")
            continue

    sitemap_count = len(tokens)
    if sitemap_count == 0:
        print("Sitemap unavailable — using seed list only.")
    else:
        print(f"Sitemap: {sitemap_count} companies discovered.")

    # ── Step 2: Always add seed list as supplement ─────────────────────────
    for s in SEED_TOKENS:
        add(s)

    print(f"Total companies to scan: {len(tokens)} "
          f"({sitemap_count} from sitemap + {len(tokens) - sitemap_count} from seed list)")
    return tokens


# ─── JOB FETCHING & FILTERING ─────────────────────────────────────────────────

def fetch_jobs(token: str) -> list:
    url = f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs?content=true"
    try:
        r = requests.get(url, timeout=10,
                         headers={"User-Agent": "Mozilla/5.0 (compatible; job-search-bot/1.0)"})
        return r.json().get("jobs", []) if r.status_code == 200 else []
    except Exception:
        return []


def is_relevant(job: dict) -> tuple:
    title    = (job.get("title")   or "").lower()
    content  = (job.get("content") or "").lower()
    location = " ".join(loc.get("name", "") for loc in job.get("offices", [])).lower()

    if not any(kw in title for kw in TITLE_KEYWORDS):
        return False, "title_mismatch"

    for ex in EXCLUDE_KEYWORDS:
        if ex in title or ex in content[:600]:
            return False, f"excluded:{ex}"

    if location and any(x in location for x in NON_US_INDICATORS):
        if not any(kw in location or kw in title for kw in REMOTE_INDICATORS):
            return False, "non_us"

    return True, "ok"


def score_job(job: dict) -> int:
    text  = f"{job.get('title', '')} {job.get('content', '')}".lower()
    score = sum(10 for kw in HIGH_VALUE_KEYWORDS if kw in text)
    score += sum(5  for kw in MED_VALUE_KEYWORDS  if kw in text)
    return min(score, 100)


def build_url(job: dict, token: str) -> str:
    return f"https://job-boards.greenhouse.io/{token}/jobs/{job.get('id', '')}"


# ─── CSV OUTPUT ───────────────────────────────────────────────────────────────

OUTPUT_COLS = ["Date Applied", "Company", "Job Title", "Link",
               "My Follow Up", "Status", "Extra"]

def append_to_output(rows: list):
    "Append rows to output CSV; write header only if file doesn't exist yet."
    file_exists = os.path.isfile(OUTPUT_CSV)
    with open(OUTPUT_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=OUTPUT_COLS)
        if not file_exists:
            w.writeheader()
        w.writerows(rows)


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    print("\nGreenhouse Job Scraper — Maiia Kishchukova")
    print(f"Score threshold: >=  {MIN_MATCH_SCORE}  |  Target: {MAX_JOBS} qualified matches\n")

    # Load state
    seen_ids     = load_seen_ids(SEEN_FILE)
    applied_urls = load_applied_urls(APPLIED_CSV, OUTPUT_CSV)
    print()

    companies    = fetch_all_gh_companies()
    print()

    results       = []
    new_seen_ids  = set()
    skip_seen     = 0
    skip_applied  = 0
    skip_filter   = 0
    skip_score    = 0
    n_companies   = 0

    for token in companies:
        if len(results) >= MAX_JOBS:
            break

        jobs = fetch_jobs(token)
        if not jobs:
            continue

        n_companies += 1
        matched = 0

        for job in jobs:
            job_id = str(job.get("id", ""))

            # 1. Skip if already seen in a previous run
            if job_id in seen_ids:
                skip_seen += 1
                continue

            # Mark as seen regardless of outcome
            new_seen_ids.add(job_id)

            # 2. Build URL and skip if already applied
            url  = build_url(job, token)
            norm = _norm(url)
            if any(norm == u or norm in u or u in norm for u in applied_urls):
                skip_applied += 1
                continue

            # 3. Title / exclusion / location filter
            ok, reason = is_relevant(job)
            if not ok:
                skip_filter += 1
                continue

            # 4. Score gate
            score = score_job(job)
            if score < MIN_MATCH_SCORE:
                skip_score += 1
                continue

            location = ", ".join(
                loc.get("name", "") for loc in job.get("offices", [])
            ) or "Remote / Not specified"

            results.append({
                "Date Applied": "",
                "Company":      token.replace("-", " ").title(),
                "Job Title":    job.get("title", ""),
                "Link":         url,
                "My Follow Up": "",
                "Status":       "",
                "Extra":        f"Score:{score} | {location}",
            })
            matched += 1

            if len(results) >= MAX_JOBS:
                break

        if matched > 0 or len(jobs) > 0:
            icon = ">" if matched > 0 else " "
            print(f"  {icon} {token:<32} {len(jobs):>3} jobs | "
                  f"{matched} matched  (total: {len(results)}/{MAX_JOBS})")

        time.sleep(REQUEST_DELAY)

    # Sort best matches first, then write
    results.sort(
        key=lambda r: int(m.group(1)) if (m := re.search(r"Score:(\d+)", r["Extra"])) else 0,
        reverse=True,
    )
    append_to_output(results)

    # Persist all newly seen IDs (matched AND unmatched) so next run skips them
    save_seen_ids(SEEN_FILE, new_seen_ids)

    # Summary
    print(f"\n{'─'*62}")
    if len(results) >= MAX_JOBS:
        print(f"Goal reached: {len(results)} qualified jobs appended to {OUTPUT_CSV}")
    else:
        print(f"Scan complete: {len(results)}/{MAX_JOBS} qualified jobs found.")
        print(f"  Add more company tokens or re-run after new jobs are posted.")
        print(f"  Output appended to {OUTPUT_CSV}")
    print(f"  Skipped (seen before):   {skip_seen}")
    print(f"  Skipped (already applied): {skip_applied}")
    print(f"  Skipped (filter):        {skip_filter}")
    print(f"  Skipped (low score):     {skip_score}")
    print(f"  New IDs added to cache:  {len(new_seen_ids)}")
    print(f"  Companies scanned:       {n_companies}")
    if results:
        t = results[0]
        print(f"\nTop match: {t['Job Title']} @ {t['Company']}  [{t['Extra']}]")
        print(f"  {t['Link']}")
    print(f"\nImport into Google Sheets:")
    print(f"  File -> Import -> Upload {OUTPUT_CSV} -> Append to current sheet")
"""

if __name__ == "__main__":
    imain()

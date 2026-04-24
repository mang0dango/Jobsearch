# ─── GENERAL SETTINGS ─────────────────────────────────────────────────────────

MIN_NUMBER_OF_SKILLS_MATCHED = 3 
REQUEST_DELAY                = 0.25
PAGES_TO_LOAD                = 100

# ─── FILE PATHS ──────────────────────────────────────────────────────────────

UNFILTERED_JOBS     = "../data/unfiltered_jobs.csv"
PROCESSED_JOBS      = "../data/processed_jobs.csv"
APPROVED_JOBS       = "../data/approved_jobs.csv"
REJECTED_JOBS       = "../data/rejected_jobs.csv"

# ─── FILTERS ─────────────────────────────────────────────────────────────────

# Go to the greenhouse website, search for the type of job you want and set filters such as remote, or the location you want. Copy and paste the links here. 
GREENHOUSE_SEARCHES = ("https://my.greenhouse.io/jobs?query=software%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=software%20developer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=data%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=AI%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=AI%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=python%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote", "https://my.greenhouse.io/jobs?query=software%20engineer&location=Michigan%2C%20USA&lat=43.924812&lon=-84.633107&location_type=region&country_short_name=US&state_short_name=MI&work_type[]=remote")

# Any jobs with a few of these skills listed will be seen as a good match.
SKILL_KEYWORDS = [
    "python", "aws", "snowflake", "airflow", "sql", "database"
    "data engineer", "machine learning", "ai", "kubernetes", "docker",
    "docker", "postgresql", "dynamodb", "terraform", "bash",
    "linux", "rest api", "ci/cd", "gitlab", "backend", "data pipeline",
    "dbt", "ml","cloud", "cloud platforms", "generative intelligence", 
    "airflow", "dbt", "etl", "data", "queries", "query", "programming", 
    "program", "big date", "api", "coding", "unix", "command line", 
    "terminal", "kotlin", "java", "snowflake", "data warehousing",
    "yaml", "csv", "containerization", "aws tools" , "ec2", "pipeline",
    "pipelines", "ci/cd", "github", "gitlab", "automate", "automation",
    "unix administration", "continuous delivery", "cloud computing", 
    "test", "pytest", "data structures", "json", "devops", "lambda",
    "gcp"
]

# Any jobs with these words in the title or description will be filtered out.
BLACKLIST_KEYWORDS = [
    "internship", "internship", "co-op", "coop", "co op",
    "senior", "sr.", "sr", "lead engineer", "lead developer",
    "staff engineer", "principal engineer", "founding engineer",
    "director", "vp ", "manager", "tech lead",
    "5+ years", "6+ years", "7+ years", "8+ years",
    "frontend", "ios developer", "hardware developer",
    "ruby on rails", ".net developer", "php developer", 
    "web design", "data scientist", "web development",
    "front-end", "project management", "hardware engineer",
    "data entry",
]

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN",
    "IA","KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV",
    "NH","NJ","NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN",
    "TX","UT","VT","VA","WA","WV","WI","WY"
]

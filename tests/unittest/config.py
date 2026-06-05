# ─── GENERAL SETTINGS ─────────────────────────────────────────────────────────

MIN_NUMBER_OF_SKILLS_MATCHED = 3 
REQUEST_DELAY                = 0.25
MAX_JOB_COUNT_PER_QUERY      = 25

# ─── FILE PATHS ──────────────────────────────────────────────────────────────

FETCHED_JOBS      = "../test/data/fetched_jobs.csv"
PROCESSED_JOBS    = "../test/data/processed_jobs.csv" 
APPROVED_JOBS     = "../test/data/approved_jobs.csv" 
REJECTED_JOBS     = "../test/data/rejected_jobs.csv"
UNFILTERED_JOBS   = "../test/data/unfiltered_jobs.cvs"
UNKNOWN_QUESTIONS = "../test/data/unknown_questions.csv" 

# ─── FILTERS ─────────────────────────────────────────────────────────────────

GREENHOUSE_SEARCHES = ["fakelink1", "fakelink2", "fakelink3"]

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
    "gcp", "documentation", "best practice", "security groups", "iam",
    "permissions", "container", "networking", "git", "django", "llm",
    "kotlin", "java", "android",  
]

# Automatically filter out jobs with these job experience markers.
BLACKLIST_EXPERIENCE_KEYWORDS = [
    "senior", "architect", "software engineer iii",
    "lead software engineer", "senior software engineer",
    "sr.", "sr", "lead engineer", "lead developer",
    "senior full stack engineer", "staff engineer",
    "principal engineer", "principal software engineer",
    "founding engineer", "director", "vp", "manager",
    "tech lead", "5+ years", "6+ years", "7+ years", "8+ years", "5-6 years"
    "lead python engineer", "staff software engineer", "senior AI", "staff data engineer", "principal platform engineer", "senior software developer", "security engineer", "Principal AI", "senior developer", "principal solutions engineer"
]

# Automatically filter out jobs with this skill or niche listed.
BLACKLIST_SKILL_KEYWORDS = [
    "frontend", "ios developer", "hardware developer",
    ".net developer", "php developer", 
    "web design", "data scientist", "web development",
    "front-end", "project management", "hardware engineer",
    "data entry","active secret clearance",
    "government clearance required", "secret clearance required",
]

# Blacklist experience keywords are double checked against this list for context..
COLLABORATIVE_KEYWORDS = [
    "work with", "collaborate with", "mentor", "onboard", "help", 
    "coordinate with", "learn from", "work alongside", "report to", 
    "interact with", "engage with", "communicate", "consult with", 
    "mentored", "learn from", "contribute to", "participate in",
    "work closely with", "assist", "collaboration", "founded by",
    "team", "leadership", "establish", "decision" ," decisions",
    "design", "development", "develop", "practices", "work alongside",
    "together", "teams", "cross",
]

# ─── job application difficulty estimator marks ───────────────────────────────────────────────────────────

BOILERPLATE_QUESTIONS = [
    'first name', 'last name', 'preferred first name', 'email',
    'phone', 'start date year', 'end date year', 'linkedin profile',
    'website', 'country', 'school', 'degree', 'discipline', 'start date month',
    'end date month', 'gender', 'are you hispanic/latino?', 'veteran status',
    'disability status',
]
EASY_KEY_PHRASES = ["name", "full name", "refer", "referred", "hear about", "time", "country", "reside", "located", "address", "know", "family members", "related to", "related by", "relative", "employee", "employed", "have you", "right to work", "proof", "documented", "documentation", "conflict", "compete" ,"review and acknowledge", "disability", "gender", "racial", "ethnic", "veteran", "linkedin", "immigration", "authorized", "legal", "legally", "sponsorship", "location", "citizen", "greencard", "location", "city", "state", "states", "live in", "years of", "professional experience", "working experience", "degree", "graduate", "are you", "do you", "currently", "member", "privacy", "agreement", "statement", "would you", "how", "restoraunt", "pet", "hobby", "outside of work", "free time", "hobbies", "is it", "can you", "confirm"]
MEDIUM_KEY_PHRASES = ["why", "favorite", "salary", "protocols", "rate", "which", "tools", "expectation", "compensation", "list", "rate", "indicate", "select", "what"]
HARD_KEY_PHRASES = ["how would you", "join", "what would you do", "explain", "tell", "apply to", "references", "made you", "decide", "example", "examples", "result", "impact", "which", "used", "mission", "values", "describe", "in detail", "description"]
ALL_KEY_PHRASES = BOILERPLATE_QUESTIONS + EASY_KEY_PHRASES + MEDIUM_KEY_PHRASES + HARD_KEY_PHRASES


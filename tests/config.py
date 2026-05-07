MIN_NUMBER_OF_SKILLS_MATCHED = 3 

PAGES_TO_LOAD = []

UNFILTERED_JOBS = "test/path1.py"
PROCESSED_JOBS  = "test/path2.py"
APPROVED_JOBS   = "test/path3.py"
REJECTED_JOBS   = "test/path4.py"

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
    "senior", "internship", "architect", "software engineer iii",
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

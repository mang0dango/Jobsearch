from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv

URL = "https://my.greenhouse.io/jobs?query=software%20engineer&location=United%20States&lat=39.71614&lon=-96.999246&location_type=country&country_short_name=US&work_type[]=remote"

options = Options()
options.add_argument("--headless=new")
options.add_argument("--window-size=1920,1080")

driver = webdriver.Chrome(options=options)
wait = WebDriverWait(driver, 15)

driver.get(URL)

# Wait for jobs to load
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-testid='job-posting']")))

# Scroll to load more jobs
last_height = driver.execute_script("return document.body.scrollHeight")

for _ in range(10):
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(2)

    new_height = driver.execute_script("return document.body.scrollHeight")
    if new_height == last_height:
        break
    last_height = new_height

# Extract company names
companies = set()

job_cards = driver.find_elements(By.CSS_SELECTOR, "[data-testid='job-posting']")

for job in job_cards:
    try:
        try:
            company = job.find_element(By.CSS_SELECTOR, "[data-testid='company-name']").text
        except:
            company = job.find_element(By.CSS_SELECTOR, "div:nth-child(1)").text

        company = company.strip()

        if company:
            companies.add(company)

    except:
        continue

driver.quit()

# Sort results
new_companies = sorted(companies)
print(f"\nThere are {len(new_companies)} new companies.")

# 📝 Save to TXT
with open("companies.txt", "rw", encoding="utf-8") as f:
    previous = f.read()
    old_companies = {item.strip() for item in previous.split(",") if item.strip()}
    all_companies = old_companies.union(new_companies)
    f.write(", ".join(all_companies))

print(f"Saved {len(all_companies)} companies to companies.txt and companies.csv")

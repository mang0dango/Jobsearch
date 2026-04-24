from bs4 import BeautifulSoup
from urllib.parse import urlparse
import re

# -----------------------------
# Extract links from Google HTML
# -----------------------------
def extract_links_from_html(file="results.html"):
    with open(file, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    links = []
    print(f"\n number of links: {len(links)}\n")

    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Google result links often look like:
        # /url?q=https://boards.greenhouse.io/company/jobs/123...
        match = re.search(r"/url\?q=(https://boards\.greenhouse\.io[^&]+)", href)
        if match:
            links.append(match.group(1))

    return links

# -----------------------------
# Extract company name
# -----------------------------
def extract_company(url: str):
    try:
        if "boards.greenhouse.io" not in url:
            return None

        parts = urlparse(url).path.strip("/").split("/")

        if len(parts) >= 1:
            company = parts[0]
            if company not in ["jobs", "careers"]:
                return company
            return None
    except:
        return None

# -----------------------------
# MAIN
# -----------------------------
def main():
    links = extract_links_from_html()

    companies = set()

    for link in links:
        company = extract_company(link)
        print(f"company: {company}")
        if company:
            companies.add(company)

    print("\n=== UNIQUE COMPANIES ===")
    for c in sorted(companies):
        print(c)

    print(f"\nTotal companies: {len(companies)}")

if __name__ == "__main__":
    main()

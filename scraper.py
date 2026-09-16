import sys
import json
from playwright.sync_api import sync_playwright

def scrape_indeed(page, keyword, location, max_jobs=20):
    jobs = []
    per_page = 15
    pages_needed = (max_jobs // per_page) + 1
    
    for page_num in range(pages_needed):
        start = page_num * 10
        url = f"https://ph.indeed.com/jobs?q={keyword.replace(' ', '+')}&l={location.replace(' ', '+')}&start={start}"
        print(f"Scraping Indeed page {page_num + 1}: {url}", file=sys.stderr)
        page.goto(url, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(5000)
        
        cards = page.query_selector_all("div.job_seen_beacon")
        print(f"Found {len(cards)} Indeed cards on page {page_num + 1}", file=sys.stderr)
        if not cards:
            break
        
        for card in cards:
            if len(jobs) >= max_jobs:
                break
            try:
                # Title: <span id="jobTitle-faf755ec8d5fda48" title="...">
                title = "Unknown"
                for sel in ["span[id^='jobTitle-']", "h3.jobTitle a span[title]", "h3.jobTitle a", "h3.jobTitle"]:
                    el = card.query_selector(sel)
                    if el:
                        text = el.get_attribute("title") or el.inner_text()
                        if text and text.strip():
                            title = text.strip()
                            break
                
                # Company: <span data-testid="company-name">
                company_el = card.query_selector("span[data-testid='company-name']")
                company = company_el.inner_text().strip() if company_el else "Unknown"
                
                # Location: <div data-testid="text-location">
                location_el = card.query_selector("div[data-testid='text-location']")
                loc = location_el.inner_text().strip() if location_el else location
                
                # URL: <a data-jk="..." class="jcs-JobTitle">
                job_id = ""
                for sel in ["a[data-jk]", "a.jcs-JobTitle", "h3.jobTitle a"]:
                    link_el = card.query_selector(sel)
                    if link_el:
                        jk = link_el.get_attribute("data-jk")
                        if jk:
                            job_id = jk
                            break
                        # Fallback: extract from href
                        href = link_el.get_attribute("href") or ""
                        if "jk=" in href:
                            job_id = href.split("jk=")[1].split("&")[0]
                            break
                
                url_final = f"https://ph.indeed.com/viewjob?jk={job_id}" if job_id else ""
                
                # Work mode from location text
                loc_lower = loc.lower()
                if "remote" in loc_lower:
                    work_mode = "Remote"
                elif "hybrid" in loc_lower:
                    work_mode = "Hybrid"
                else:
                    work_mode = "On-site"
                
                jobs.append({
                    "title": title,
                    "company": company,
                    "location": loc,
                    "url": url_final,
                    "source": "Indeed",
                    "work_mode": work_mode,
                    "description": "",
                    "posted_at": ""
                })
            except Exception as e:
                print(f"Error parsing Indeed card: {e}", file=sys.stderr)
    
    return jobs

def scrape_jobstreet(page, keyword, location, max_jobs=20):
    jobs = []
    keyword_slug = keyword.replace(' ', '-').lower()
    location_slug = location.replace(' ', '-').lower()
    url = f"https://ph.jobstreet.com/{keyword_slug}-jobs/in-{location_slug}"
    print(f"Scraping JobStreet: {url}", file=sys.stderr)
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(5000)
    
    cards = page.query_selector_all("article[data-card-type='JobCard'], div[data-automation='normalJob']")
    print(f"Found {len(cards)} JobStreet cards", file=sys.stderr)
    
    for card in cards[:max_jobs]:
        try:
            title_el = card.query_selector("a[data-automation='jobTitle'], h3 a, a[class*='jobTitle']")
            company_el = card.query_selector("a[data-automation='jobCompany'], span[class*='companyName']")
            location_el = card.query_selector("a[data-automation='jobLocation'], span[class*='location']")
            link_el = card.query_selector("a[data-automation='jobTitle'], h3 a")
            
            href = link_el.get_attribute("href") if link_el else ""
            if href and not href.startswith("http"):
                href = "https://ph.jobstreet.com" + href
            
            jobs.append({
                "title": title_el.inner_text().strip() if title_el else "Unknown",
                "company": company_el.inner_text().strip() if company_el else "Unknown",
                "location": location_el.inner_text().strip() if location_el else location,
                "url": href,
                "source": "JobStreet",
                "work_mode": "On-site",
                "description": "",
                "posted_at": ""
            })
        except Exception as e:
            print(f"Error parsing JobStreet card: {e}", file=sys.stderr)
    return jobs

def main():
    # Parse args: python scraper.py <keyword> <location> [site]
    keyword = sys.argv[1] if len(sys.argv) > 1 else "Web Developer"
    location = sys.argv[2] if len(sys.argv) > 2 else "Manila"
    site = sys.argv[3] if len(sys.argv) > 3 else "both"  # both | indeed | jobstreet

    all_jobs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-PH"
        )
        page = context.new_page()

        if site in ("indeed", "both"):
            all_jobs.extend(scrape_indeed(page, keyword, location))
        
        if site in ("jobstreet", "both"):
            all_jobs.extend(scrape_jobstreet(page, keyword, location))

        browser.close()

    # Print ONLY clean JSON to stdout (debug goes to stderr)
    print(json.dumps(all_jobs))

if __name__ == "__main__":
    main()
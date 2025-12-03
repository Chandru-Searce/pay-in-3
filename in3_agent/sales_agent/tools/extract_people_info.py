# Import necassary packages
import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load env variables
load_dotenv()

# Environment variables
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY2")
PEOPLE_SEARCH_API_URL = os.getenv("PEOPLE_SEARCH_API")

# Destination file
DESTINATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "lead_data",
    "people-info.json"
)


# --------------------- FUNCTION TO FETCH 1 DOMAIN ---------------------

def _fetch_people_by_domain(domain: str) -> List[dict]:
    """Fetch leads for a single domain. Domain must be wrapped inside a list."""

    payload = {
        "person_titles": ["E-commerce Manager", "Marketing Manager", "Sales Manager", "CEO", "Owner", "Founder"],
        "q_organization_domains_list": [domain],
        "include_similar_titles": True,
        "per_page": 100
    }

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY
    }

    try:
        response = requests.post(PEOPLE_SEARCH_API_URL, headers=headers, json=payload)
        data = response.json()
    except Exception:
        print(f"❌ Failed fetching domain: {domain}")
        return []

    people = []

    for person in data.get("people", []):
        org = person.get("organization", {})

        lead = {
            "lead_title": f"{org.get('name', '')} - Lead",
            "organization_name": org.get("name", ""),
            "organization_id": person.get("organization_id", ""),
            "website_url": org.get("website_url", ""),
            "person_name": person.get("name", ""),
            "person_first_name": person.get("first_name", ""),
            "person_last_name": person.get("last_name", ""),
            "person_email": person.get("email", ""),
            "person_title": person.get("title", ""),
            "organization_phone_number": org.get("primary_phone", {}).get("number", ""),
            "person_linkedin_url": person.get("linkedin_url", ""),
            "person_facebook_url": person.get("facebook_url", ""),
            "person_github_url": person.get("github_url", "")
        }

        people.append(lead)

    print(f"✅ Completed: {domain} → {len(people)} leads")
    return people


# --------------------- MAIN FUNCTION ---------------------

def _extract_people_info(domain_list: List[str]):
    """Run each domain in parallel and save combined results."""

    all_results = []

    # Run requests in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_fetch_people_by_domain, domain): domain for domain in domain_list}

        for future in as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                all_results.extend(result)   # append results from each domain
            except Exception as e:
                print(f"❌ Error processing domain {domain}: {e}")

    # Save all combined results
    os.makedirs(os.path.dirname(DESTINATION_FILE_PATH), exist_ok=True)

    with open(DESTINATION_FILE_PATH, "w") as file:
        json.dump(all_results, file, indent=4)

    print(f"\n💾 Saved {len(all_results)} leads → {DESTINATION_FILE_PATH}")

    return all_results


# with open("/home/chandru/Chandru/in3/in3_agent/sales_agent/lead_data/company-info.json", "r") as file:
#     company_data = json.load(file)

# domains = [company['primary_domain'] for company in company_data]

# _extract_people_info(domain_list=domains[:20])
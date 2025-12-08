# Import necassary packages
import os
import json
import requests
from typing import List
from dotenv import load_dotenv
from .bulk_people_enrichment import _people_enrichment_bulk
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load env variables
load_dotenv()

# Environment variables
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY2")
PEOPLE_SEARCH_API_URL = os.getenv("PEOPLE_SEARCH_API")

# Destination file
DESTINATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "lead_data", "people-info.json"
)


def _fetch_people_by_domain(domain: str) -> List[dict]:
    """Fetch leads for a single domain. Domain must be wrapped inside a list."""

    payload = {
        "person_titles": [
            "E-commerce Manager",
            "Marketing Manager",
            "Sales Manager",
            "CEO",
            "Owner",
            "Founder",
        ],
        "q_organization_domains_list": [domain],
        "include_similar_titles": True,
        "per_page": 100,
    }

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": APOLLO_API_KEY,
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
            "person_github_url": person.get("github_url", ""),
        }

        people.append(lead)

    print(f"✅ Completed: {domain} → {len(people)} leads")
    return people


def extract_people_info():
    """Run each domain in parallel and save combined results."""

    COMPANY_DOMAINS_FILE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "lead_data",
        "final-leads-without-enrichment.json",
    )

    with open(COMPANY_DOMAINS_FILE_PATH, "r") as file:
        domain_list = json.load(file)

    all_results = []

    # Run requests in parallel
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(_fetch_people_by_domain, domain): domain
            for domain in domain_list
        }

        for future in as_completed(futures):
            domain = futures[future]
            try:
                result = future.result()
                all_results.extend(result)  # append results from each domain
            except Exception as e:
                print(f"❌ Error processing domain {domain}: {e}")

    print("\n Start to enrich the lead details")

    enriched_leads = _people_enrichment_bulk(all_results)

    return enriched_leads

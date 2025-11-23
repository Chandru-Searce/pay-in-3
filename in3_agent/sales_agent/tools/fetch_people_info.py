# Import necassary packages
import os
import json
import requests
from typing import List, Tuple
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Environment variables
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY2")
PEOPLE_SEARCH_API_URL = os.getenv("PEOPLE_SEARCH_API")

PAGE_TRACKER_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lead_data", "page-tracker.json")
BATCH_SIZE = 5
MAX_PAGE = 2000

# Filter crieterias
person_titles :List[str] = ["E-commerce Manager","Marketing Manager", "Sales Manager"]
organization_location :List[str] = ["netherlands"]

DETINATION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lead_data", "people-info.json")

# ---------------------- PAGE TRACKING FUNCTIONS ----------------------

def _load_visited_ranges() -> List[Tuple[int, int]]:
    """Load visited page ranges from file. If not found, return empty list."""
    if not os.path.exists(PAGE_TRACKER_FILE):
        return []
    with open(PAGE_TRACKER_FILE, "r") as f:
        return json.load(f)


def _save_visited_ranges(ranges: List[Tuple[int, int]]):
    """Save visited ranges to JSON file."""
    with open(PAGE_TRACKER_FILE, "w") as f:
        json.dump(ranges, f, indent=4)


def _get_next_page_range() -> Tuple[int, int]:
    """
    Returns the next page range (5 pages at a time)
    and ensures it will never give the same range again.
    """
    visited = _load_visited_ranges()

    if not visited:
        start = 1
    else:
        last_start, last_end = visited[-1]
        start = last_end + 1

    if start > MAX_PAGE:
        raise ValueError("All pages up to MAX_PAGE have been processed.")

    end = min(start + BATCH_SIZE - 1, MAX_PAGE)

    # Store range
    visited.append([start, end])
    _save_visited_ranges(visited)

    return start, end

# ---------------------- APOLLO SCRAPER FUNCTION ----------------------

def _scrape_apollo_pages(start_page: int, end_page: int):
    print(f"\n🚀 Scraping pages {start_page} → {end_page}")

    lead_list = []

    for page_number in range(start_page, end_page + 1):
        print(f"Fetching page {page_number}")

        payload = {
            "person_titles": person_titles,
            "organization_locations": organization_location,
            "include_similar_titles": True,
            "per_page": 100,
            "page": page_number
        }

        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY
        }

        response = requests.post(PEOPLE_SEARCH_API_URL, headers=headers, json=payload)

        try:
            data = response.json()
        except Exception:
            print(f"❌ Failed to parse JSON for page {page_number}")
            continue

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
                "person_phone_number": org.get("primary_phone", {}).get("number", ""),
                "person_linkedin_url": person.get("linkedin_url", ""),
                "person_facebook_url": person.get("facebook_url", ""),
                "person_github_url": person.get("github_url", "")
            }

            lead_list.append(lead)

    # Save results
    with open(DETINATION_FILE_PATH, "w") as f:
        json.dump(lead_list, f, indent=4)

    print(f"✅ Saved {len(lead_list)} leads → {DETINATION_FILE_PATH}")


def _extract_people_info():
    start, end = _get_next_page_range()
    _scrape_apollo_pages(start, end)

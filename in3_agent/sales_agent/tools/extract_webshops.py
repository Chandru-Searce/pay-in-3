# Import necessary packages
import os
import json
import requests
from typing import List, Tuple
from dotenv import load_dotenv
from google.cloud import storage

# Load env variables
load_dotenv()

# Environment variables
APOLLO_API_KEY = os.getenv("APOLLO_API_KEY2")
ORGANIZATION_SEARCH_API = os.getenv("ORGANIZATION_SEARCH_API")

# GCS bucket settings
GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
GCS_PAGE_TRACKER_BLOB = "page-tracker.json"

BATCH_SIZE = 5
MAX_PAGE = 5000

# Filter criteria
organization_location: List[str] = ["netherlands"]

DESTINATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "lead_data",
    "company-info.json"
)


# ---------------------- GCS UTILITY FUNCTIONS ----------------------

def _get_gcs_client():
    return storage.Client()

def _load_visited_ranges() -> List[Tuple[int, int]]:
    """Load visited page ranges from GCS JSON file."""
    client = _get_gcs_client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(GCS_PAGE_TRACKER_BLOB)

    if not blob.exists():
        return []

    data = blob.download_as_text()
    return json.loads(data)


def _save_visited_ranges(ranges: List[Tuple[int, int]]):
    """Save visited page ranges to GCS JSON file."""
    client = _get_gcs_client()
    bucket = client.bucket(GCS_BUCKET_NAME)
    blob = bucket.blob(GCS_PAGE_TRACKER_BLOB)

    blob.upload_from_string(
        json.dumps(ranges, indent=4),
        content_type="application/json"
    )


def _get_next_page_range() -> Tuple[int, int]:
    """Returns the next page range (5 pages at a time)."""
    visited = _load_visited_ranges()

    if not visited:
        start = 1
    else:
        last_start, last_end = visited[-1]
        start = last_end + 1

    if start > MAX_PAGE:
        raise ValueError("All pages up to MAX_PAGE have been processed.")

    end = min(start + BATCH_SIZE - 1, MAX_PAGE)

    visited.append([start, end])
    _save_visited_ranges(visited)

    return start, end


# ---------------------- APOLLO SCRAPER FUNCTION ----------------------

def _scrape_apollo_pages(start_page: int, end_page: int):
    print(f"\n🚀 Scraping pages {start_page} → {end_page}")

    all_results = []

    for page_number in range(start_page, end_page + 1):
        print(f"Fetching page {page_number}")

        # Build payload with conditional per_page
        payload = {
            "organization_locations": organization_location,
            "page": page_number
        }

        if page_number <= 500:
            payload["per_page"] = 100

        headers = {
            "accept": "application/json",
            "Cache-Control": "no-cache",
            "Content-Type": "application/json",
            "x-api-key": APOLLO_API_KEY
        }

        response = requests.post(ORGANIZATION_SEARCH_API, headers=headers, json=payload)
        print(response)
        # print(response.status_code)
        try:
            data = response.json()

            organizations = data.get("organizations", "")
            
            for org in organizations:

                company_details = {
                    "organization_name": org.get("name", ""),
                    "website_url": org.get("website_url", ""),
                    "primary_domain": org.get("primary_domain", "")

                }

                all_results.append(company_details)

        except Exception:
            print(f"❌ Failed to parse JSON for page {page_number}")
            continue

    # Save results locally (you can also move this to GCS if you want)
    with open(DESTINATION_FILE_PATH, "w") as f:
        json.dump(all_results, f, indent=4)

    print(f"✅ Saved {len(all_results)} organization details → {DESTINATION_FILE_PATH}")


# ---------------------- MAIN EXTRACTOR FUNCTION ----------------------
def _extract_webshops_info():
    start, end = _get_next_page_range()
    results = _scrape_apollo_pages(start, end)
    print(results)

_extract_webshops_info()
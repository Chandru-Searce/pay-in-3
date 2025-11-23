# Import packaegs
import os
import json
import requests
from dotenv import load_dotenv

# Load Environment variables
load_dotenv()

# Environment variables
PEOPLE_ENRICHMENT_API = os.getenv("PEOPLE_ENRICHMENT_API")
API_KEY = os.getenv("APOLLO_API_KEY2")

DESTINATION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lead_data", "final-leads-with-enrichment.json")

def _people_enrichment(lead_data_without_enrichment):
    """
    This function help us to enrich the lead data that we got from the
    People Search API. It will enrich the data with proper email id.
    
    Note: It may and may not enrich the data.
    """

    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    lead_list = []

    for lead in lead_data_without_enrichment:

        payload = {
            "first_name": lead.get("person_first_name", ""),
            "last_name": lead.get("person_last_name", ""),
            "organization_name": lead.get("organization_name", ""),
            "name": lead.get("person_name", "")
        }


        response = requests.post(PEOPLE_ENRICHMENT_API, headers=headers, json=payload)

        try:
            data = response.json()
            print(data)
        except Exception:
            print(f"❌ Failed to parse JSON for page")
            continue

        persons = data.get("person", {})

        # Normalize to list
        if isinstance(persons, dict):
            persons = [persons]

        for person in persons:
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
    with open(DESTINATION_FILE_PATH, "w") as f:
        json.dump(lead_list, f, indent=4)

    return lead_list
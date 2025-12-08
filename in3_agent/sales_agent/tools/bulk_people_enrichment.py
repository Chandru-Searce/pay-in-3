# Import packaegs
import os
import json
import requests
from math import ceil
from dotenv import load_dotenv
from google.cloud import storage

# Load .env variables
load_dotenv()

PEOPLE_BULK_ENRICHMENT_API = os.getenv("PEOPLE_BULK_ENRICHMENT_API")
API_KEY = os.getenv("APOLLO_API_KEY2")

DESTINATION_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..",
    "lead_data",
    "final-leads-with-enrichment.json",
)

def _save_fetched_domains_to_gcs(leads):
    """
    Save the leads data to GCS Bucket.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    blob_name = "final-leads-with-enrichment.json"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        json.dumps(leads, indent=4), content_type="application/json"
    )

    print(f"✅ Saved {len(leads)} leads to gs://{bucket_name}/{blob_name}")


def _people_enrichment_bulk(lead_data_without_enrichment):
    headers = {
        "accept": "application/json",
        "Cache-Control": "no-cache",
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
    }

    lead_list = []

    batch_size = 10
    num_batches = ceil(len(lead_data_without_enrichment) / batch_size)

    for batch_index in range(num_batches):
        batch = lead_data_without_enrichment[
            batch_index * batch_size : (batch_index + 1) * batch_size
        ]

        details_payload = []
        for lead in batch:
            details_payload.append(
                {
                    "first_name": lead.get("person_first_name", ""),
                    "last_name": lead.get("person_last_name", ""),
                    "organization_name": lead.get("organization_name", ""),
                    "name": lead.get("person_name", ""),
                }
            )

        payload = {
            "details": details_payload,
            "reveal_personal_emails": False,
            "reveal_phone_number": False,
        }

        try:
            response = requests.post(
                PEOPLE_BULK_ENRICHMENT_API, headers=headers, json=payload
            )
            data = response.json()
        except Exception as e:
            print(f"❌ Failed to fetch bulk enrichment batch {batch_index + 1}: {e}")
            continue

        results = data.get("matches", [])

        # Safety: if results are missing or length mismatches
        if not results or not isinstance(results, list):
            print(f"⚠ No enrichment results for batch {batch_index + 1}")
            continue

        # Loop through results (each corresponds to inputs)
        for i, person in enumerate(results):
            original_lead = batch[i]

            # If match not found (Apollo returns null)
            if person is None:
                print(f"⚠ No match found for: {original_lead.get('person_name')}")
                continue

            org = (
                person.get("organization", {})
                if isinstance(person.get("organization", {}), dict)
                else {}
            )

            enriched_lead = {
                "lead_title": f"{org.get('name', '')} - Lead",
                "organization_name": org.get(
                    "name", original_lead.get("organization_name", "")
                ),
                "organization_id": person.get(
                    "organization_id", original_lead.get("organization_id", "")
                ),
                "website_url": org.get("website_url", ""),
                "person_name": person.get("name", ""),
                "person_first_name": person.get("first_name", ""),
                "person_last_name": person.get("last_name", ""),
                "person_email": person.get("email", ""),
                "person_title": person.get("title", ""),
                "organization_phone_number": org.get("primary_phone", {}).get(
                    "number", ""
                ),
                "person_linkedin_url": person.get(
                    "linkedin_url", original_lead.get("person_linkedin_url", "")
                ),
                "person_facebook_url": person.get(
                    "facebook_url", original_lead.get("person_facebook_url", "")
                ),
                "person_github_url": person.get(
                    "github_url", original_lead.get("person_github_url", "")
                ),
            }

            lead_list.append(enriched_lead)

    with open(DESTINATION_FILE_PATH, "w") as f:
        json.dump(lead_list, f, indent=4)

    _save_fetched_domains_to_gcs(leads=lead_list)

    return {
        "status": "sucessfull",
        "message": "The leads have been successfully stored in the GCS bucket. Location: https://storage.cloud.google.com/sales_agent_artifacts/final-leads-with-enrichment.json",
    }

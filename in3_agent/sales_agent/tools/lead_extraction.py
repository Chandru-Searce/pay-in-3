# Import necassary packages
import os
import json
from google.cloud import storage
from .extract_webshop_urls import get_webshop_urls
from .filters import _process_price_filter, _process_prohibted_items_filter

def _save_fetched_domains_to_gcs(domains: list):
    """
    Save the fetched domains from the Google Search API to GCS bucket.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    blob_name = "webshop_urls.json"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        json.dumps(domains, indent=4),
        content_type="application/json"
    )

    print(f"✅ Saved {len(domains)} domains to gs://{bucket_name}/{blob_name}")

def lead_extraction(segment: str):
    """
    Extract and filter lead data based on a specified business segment.

    This tool retrieves, filters, and compiles leads belonging to the given
    segment from the broader dataset provided by the Apollo API. The result
    is a curated collection of companies/webshops that match the requested
    segment and are ready for downstream processing, such as people-data
    extraction or CRM enrichment.

    Args:
        segment (str):
            The business or product segment for which leads should be filtered.
            This must be a valid, non-prohibited segment (e.g., Electronics,
            Fashion, Home Goods). The extraction process will only proceed if
            the segment complies with allowed categories.

    Returns:
        None:
            The function triggers a background process that saves the filtered
            lead dataset (usually as a JSON file) to cloud storage for later
            steps in the workflow.
    """

    get_webshop_urls(segment=segment)

    # Call the price filter function
    price_filtered_leads = _process_price_filter()
    print("Price filtered leads:", len(price_filtered_leads))

    # Call the prohibited items filter function
    domain_list = _process_prohibted_items_filter(price_filtering_leads=price_filtered_leads)
    print("Prohibited Items filtered leads:", len(domain_list))

    _save_fetched_domains_to_gcs(domains=domain_list)

    return {
        "status": "successful",
        "message": "The webshop URLs have been successfully stored in the GCS bucket. Location: https://storage.cloud.google.com/sales_agent_artifacts/webshop_urls.json"
    }

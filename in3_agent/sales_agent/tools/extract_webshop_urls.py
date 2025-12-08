# Import packages
import os
import json
import requests
from typing import List
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv
from google.cloud import storage
from urllib.parse import urlparse
from ..prompts.search_query_prompt import ADVANCED_SEARCH_QUERY_PROMPT
from google.genai.types import HttpOptions, GenerateContentConfig, ThinkingConfig

# ---------------- Environment ----------------
load_dotenv()

# ---------------- Gemini Setup ----------------
client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="europe-west4",
)

# File path for unqiue webshop urls
DESITINATION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lead_data", 'webshop_urls.json')
# ---------------- Models ----------------
class SearchQuery(BaseModel):
    queries: List[str]


# ---------------- Helpers ----------------
def _get_domain(url):
    """
    Extract clean domain name.
    """
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    if netloc.startswith("www."):
        netloc = netloc[4:]
    return netloc.rstrip("/")


def load_existing_domains_from_gcs() -> List[str]:
    """
    Load previously saved domains to avoid duplicates.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    blob_name = "unique_webshop_urls.json"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    if not blob.exists():
        return []

    try:
        data = json.loads(blob.download_as_text())
        if isinstance(data, list):
            return [d.lower().strip("/") for d in data]
    except:  # noqa: E722
        pass

    return []


def save_unique_domains_to_gcs(domains: list):
    """
    Save merged domain list back to GCS.
    """
    bucket_name = os.getenv("GCS_BUCKET_NAME")
    blob_name = "unique_webshop_urls.json"

    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    merged = sorted(set([d.lower().strip("/") for d in domains]))

    blob.upload_from_string(
        json.dumps(merged, indent=4),
        content_type="application/json"
    )

    print(f"✅ Saved {len(merged)} domains to gs://{bucket_name}/{blob_name}")


def inject_domain_exclusions(query: str, domains: List[str]) -> str:
    """
    Insert -site:domain filters immediately after -in3.
    This placement is necessary for proper Google filtering.
    """
    if not domains:
        return query

    exclusion_block = " ".join([f"-site:{d}" for d in domains])

    # Locate "-in3"
    idx = query.find("-in3")
    if idx != -1:
        insert_pos = idx + len("-in3")
        return query[:insert_pos] + " " + exclusion_block + query[insert_pos:]

    # Fallback: insert after "site:.nl"
    idx = query.find("site:.nl")
    if idx != -1:
        insert_pos = idx + len("site:.nl")
        return query[:insert_pos] + " " + exclusion_block + query[insert_pos:]

    # Fallback: prepend exclusions
    return exclusion_block + " " + query


def _generate_search_queries(segment: str) -> List[str]:
    """
    Generate advanced search queries using Gemini.
    """
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=f"Generate advanced search queries for: {segment}",
        config=GenerateContentConfig(
            temperature=0,
            top_k=1,
            top_p=0.9,
            system_instruction=ADVANCED_SEARCH_QUERY_PROMPT,
            thinking_config=ThinkingConfig(
                include_thoughts=False,
                thinking_budget=-1
            ),
            response_json_schema=SearchQuery.model_json_schema(),
            response_mime_type="application/json"
        ),
    )

    return json.loads(response.text).get("queries", [])


# ---------------- Main Collector ----------------
def get_webshop_urls(segment: str) -> List[str]:
    """
    - Generate queries
    - Inject exclusion URLs
    - Run Google CSE
    - Collect unique domains
    - Save incremental results to GCS
    """
    print("🔄 Loading existing domains...")
    existing_domains = load_existing_domains_from_gcs()

    print("🤖 Generating search queries using Gemini...")
    queries = _generate_search_queries(segment)

    discovered_domains = []

    for raw_query in queries:
        query = inject_domain_exclusions(raw_query, existing_domains)

        params = {
            "q": query,
            "key": os.getenv("CUSTOM_SEARCH_API"),
            "cx": os.getenv("CSE_ID"),
            "num": 10,
            "filter": "1"
        }

        try:
            response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        except Exception as ex:
            print(f"⚠️ Request failed: {ex}")
            continue

        if response.status_code != 200:
            print(f"⚠️ Google API error: {response.status_code} {response.text}")
            continue

        data = response.json()

        if "items" in data:
            for item in data["items"]:
                domain = _get_domain(item.get("link"))
                discovered_domains.append(domain)

            # add newly found domains to exclusion list for next query
            existing_domains = list(set(existing_domains + discovered_domains))


    # Save only newly discovered unique domains locally
    unique_new_domains = sorted(set(discovered_domains) - set(load_existing_domains_from_gcs()))

    with open(DESITINATION_FILE_PATH, "w") as f:
        json.dump(unique_new_domains, f, indent=4)

    print(f"📁 Saved {len(unique_new_domains)} NEW unique domains to local file: webshop-urls.json")

    # Save all unique collected domains
    save_unique_domains_to_gcs(existing_domains)

# ---------------- Run Example ----------------
if __name__ == "__main__":
    urls = get_webshop_urls(segment="Electronics")
    print("\n🎉 Final unique domains collected:", len(urls))

# Import necessary packages
import os
import json
from google import genai
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel
from google.genai.types import HttpOptions
from google.genai.types import GenerateContentConfig
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()

client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="europe-west4",
)

# Response Schema
class OutputSchema(BaseModel):
    answer: Literal["yes", "no"]

# Keep your original function EXACTLY as-is (you said it's working)
def _is_not_selling_prohibited_items(org_name: str, website_url: str):
    question = f"""
    Determine whether this webshop sells ANY prohibited or restricted items 
    that violate in3 rules.

    Prohibited examples:
    - Weapons, drugs, counterfeit, illegal items
    - Adult services, adult content
    - Tobacco, vape, CBD, cannabis
    - Gambling, lottery
    - Food or perishables
    - Rentals, taxis, logistics, repair services
    - Telecom, hosting/VPN
    - Financial services, donations, political, government
    - Any item in in3's “Prohibited Items List”

    Organization: {org_name}
    Website: {website_url}

    Return ONLY JSON:
    {{"answer": "yes"}} → SAFE, no prohibited items
    {{"answer": "no"}} → UNSAFE, sells prohibited items
    """
    grounding_tool = genai.types.Tool(
        google_search=genai.types.GoogleSearch()
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=genai.types.Content(parts=[genai.types.Part(text=question)], role="user"),
        config=GenerateContentConfig(
            tools = [grounding_tool],
            response_schema=OutputSchema.model_json_schema(),
            response_mime_type="application/json",
            temperature=0.1,
            seed=42
        )
    )
    return response.text

def _safe_check_for_prohibited_items(lead):
    org_name = lead.get("organization_name", "")
    website_url = lead.get("website_url", "")

    if not website_url or not website_url.strip():
        return None

    try:
        result = _is_not_selling_prohibited_items(org_name, website_url).strip()
        if '"answer": "no"' in result:
            return lead
        else:
            None
    except Exception as e:
        return lead  # keep on error — better to review manually than lose a lead

    return None

DESTINATION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "lead_data", "final-leads-without-enrichment.json")

# Main filtering function
def _process_prohibted_items_filter(price_filtering_leads: list):
    print("Start to check the webshop is not selling the prohibited items")

    prohibited_no_leads = []

    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [
            executor.submit(_safe_check_for_prohibited_items, lead)
            for lead in price_filtering_leads
        ]

        for i, future in enumerate(as_completed(futures), 1):
            result = future.result()
            if result is not None:
                prohibited_no_leads.append(result)
    print("Prohibited items checking completed sucessfully")

    # Save results
    with open(DESTINATION_FILE_PATH, "w") as f:
        json.dump(prohibited_no_leads, f, indent=4)

    return prohibited_no_leads

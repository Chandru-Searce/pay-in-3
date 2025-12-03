# Import necessary packages
import os
import json
from typing import Literal
from dotenv import load_dotenv
from pydantic import BaseModel
from ..utils.gemini_client import gemini_client
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai.types import GenerateContentConfig, Tool, GoogleSearch

# Environment variables
load_dotenv()

SOURCE_FILE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "..", "lead_data", "company-info.json"
)

with open(SOURCE_FILE_PATH, "r", encoding="utf-8") as file:
    lead_data = json.load(file) 

client = gemini_client

# Response Schema
class OutputSchema(BaseModel):
    answer: Literal["yes", "no"]
    
# Keep your original function EXACTLY as-is (you said it's working)
def _is_products_between_fifty_and_five_thousand(org_name: str, website_url: str):
    question = f"""
    Check if this webshop sells products typically between €50 and €5000.

    Organization: {org_name}
    Website: {website_url}

    Return ONLY valid JSON:
    {{"answer": "yes"}} or {{"answer": "no"}}
    """
    grounding_tool = Tool(
        google_search=GoogleSearch()
    )

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=question,
        config=GenerateContentConfig(
            tools= [grounding_tool],
            response_schema=OutputSchema.model_json_schema(),
            response_mime_type="application/json",
            temperature=0.1,
            seed=42
        )
    )
    return response.text

# Wrapper that ensures safe concurrent calls
def _safe_price_check(lead):
    org_name = lead.get("organization_name", "")
    website_url = lead.get("website_url", "")

    if not website_url or not website_url.strip():
        return None

    try:
        result = _is_products_between_fifty_and_five_thousand(org_name, website_url)
        result = result.strip()
        if '"answer": "yes"' in result or "yes" in result.lower():
            return lead
    except Exception as e:
        print(f"Error processing {org_name} ({website_url}): {e}")
    return None


# FIXED: Now safe for threading
def _process_price_filter():
    print("Start to check the price ranges between 50 to 5000 euro\n")
    price_yes_leads = []

    # Reduce workers if you're hitting rate limits
    with ThreadPoolExecutor(max_workers=8) as executor:  # 8–10 is safe & fast
        futures = [
            executor.submit(_safe_price_check, lead)
            for lead in lead_data
        ]

        for future in as_completed(futures):
            result = future.result()
            if result is not None:
                price_yes_leads.append(result)

    print("Price checking filter completed sucessfully")
    return price_yes_leads


# Run it
if __name__ == "__main__":
    filtered_leads = _process_price_filter()
    print(filtered_leads)
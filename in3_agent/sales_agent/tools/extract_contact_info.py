# Import necassary packages
import os
import re
import json
from google import genai
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.genai.types import Tool, HttpOptions, GenerateContentConfig, ThinkingConfig, GoogleSearch

# ------------------ Setup ------------------
client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    vertexai=True,
    project="prj-in3-non-prod-svc-01",
    location="europe-west4"
)

grounding_tool = Tool(google_search=GoogleSearch())

# Create directory for storing the people's contact info
FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lead_data")

# Make the directory
os.makedirs(FOLDER_PATH, exist_ok=True)

# SYSTEM_INSTRUCTION_FILE_PATH
SYSTEM_INSTRUCTION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "system_instruction_for_contact_info.txt")

# Load the system instruction
with open(SYSTEM_INSTRUCTION_FILE_PATH, "r") as file:
    SYSTEM_PROMPT_FOR_CONTACT_EXTRACTION = file.read()
    
# ------------------ Single URL extractor ------------------
def _extract_contacts_for_url(url: str) -> Dict:
    """Extract contacts for a single webshop URL."""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=f"Find decision-maker contacts for {url}",
            config=GenerateContentConfig(
                temperature=0.5,
                system_instruction=SYSTEM_PROMPT_FOR_CONTACT_EXTRACTION,
                thinking_config=ThinkingConfig(
                    include_thoughts=False,
                    thinking_budget=-1
                ),
                tools=[grounding_tool]
            ),
        )

        raw_output = response.text.strip()
        match = re.search(r"\{.*\}", raw_output, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                return data
            except json.JSONDecodeError:
                print(f"⚠️ JSON parsing failed for {url}")
                return {"contacts": []}
        else:
            print(f"⚠️ No JSON found for {url}")
            return {"contacts": []}
    except Exception as e:
        print(f"❌ Error processing {url}: {e}")
        return {"contacts": []}
    
# ------------------ Parallel Extractor ------------------
def extract_contacts(webshop_urls: List[str], output_file: str = "contacts.json", max_workers: int = 5):
    """Extract contacts from multiple webshop URLs in parallel using ThreadPoolExecutor."""
    all_contacts = {"contacts": []}

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(_extract_contacts_for_url, url): url for url in webshop_urls}

        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                all_contacts["contacts"].extend(result.get("contacts", []))
                print(f"✅ Done: {url}")
            except Exception as e:  
                print(f"❌ Exception for {url}: {e}")

    # Output file path
    OUTPUT_FILE_PATH = os.path.join(FOLDER_PATH, output_file)
    
    # Save all contacts
    with open(OUTPUT_FILE_PATH, "w", encoding="utf-8") as f:
        json.dump(all_contacts, f, indent=2, ensure_ascii=False)

    print(f"🎯 Finished. Results saved to {output_file}")
    return all_contacts
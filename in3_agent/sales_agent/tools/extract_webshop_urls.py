# Import necassary packages
import os
import json
import random
import requests
from typing import List
from google import genai
from pydantic import BaseModel
from dotenv import load_dotenv
from google.genai.types import HttpOptions, GenerateContentConfig, ThinkingConfig

# Load the environment variables
load_dotenv()

# ------------------ Setup ------------------
client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    vertexai=True,
    project="prj-in3-non-prod-svc-01",
    location="europe-west4",
)

# Generate Search Queries
class SearchQuery(BaseModel):
    queries: List[str]

# SYSTEM INSTRUCTION FILE PATH
SYSTEM_INSTRUCTION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "prompts", "system_instruction_for_search_query.txt")

# Load the SYSTEM_INSTRUCTION
with open(SYSTEM_INSTRUCTION_FILE_PATH, 'r') as file:
    SYSTEM_PROMPT_FOR_SEARCH_QUERY = file.read()


def _generate_search_queries(n: int = 10) -> List[str]:
    """Use this tool to generate advanced search queries"""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f"Generate {n} advanced search queries for Dutch webshops",
        config=GenerateContentConfig(
            temperature=0,
            top_k=1,
            top_p=0.9,
            system_instruction=SYSTEM_PROMPT_FOR_SEARCH_QUERY,
            thinking_config=ThinkingConfig(
                include_thoughts=False,
                thinking_budget=-1
            ),
            response_json_schema=SearchQuery.model_json_schema(),
            response_mime_type="application/json"
        ),
    )
    queries = json.loads(response.text).get("queries", [])
    return queries

def get_webshop_urls() -> List[str]:
    """Use this tool to get the webshop URL's"""
    urls = []
    number_of_queries = random.randint(5, 10)
    queries = _generate_search_queries(n=number_of_queries)
    for query in queries:
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "q": query,
            "key": os.getenv("CUSTOM_SEARCH_API"),
            "cx": os.getenv("CSE_ID"),
            "num": 10,  # Maximum results we can get 10 results
            "filter": "1"
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"⚠️ Google API error for query '{query}': {response.text}")
            continue

        data = response.json()
        if "items" in data:
            for item in data["items"]:
                urls.append(item.get("link"))
    return list(set(urls))
# Import necessary packages
import os
import json
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Get the API key from env variables
PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")

BASE_URL = "https://api.pipedrive.com/api/v2/persons"

def get_persons_v2(api_token: str = PIPEDRIVE_API_KEY,
                   filter_id: int = None,
                   ids: str = None,
                   owner_id: int = None,
                   org_id: int = None,
                   updated_since: str = None,
                   updated_until: str = None,
                   include_fields: str = None,
                   custom_fields: str = None,
                   limit: int = 50,
                   cursor: str = None):
    """
    Fetch persons from Pipedrive API (v2).
    Optional filters include filter_id, ids, owner_id, org_id, updated_since, updated_until, etc.
    """
    headers = {
        "Accept": "application/json"
    }
    
    # Build query params dynamically
    params = {
        "api_token": api_token,
        "filter_id": filter_id,
        "ids": ids,
        "owner_id": owner_id,
        "org_id": org_id,
        "updated_since": updated_since,
        "updated_until": updated_until,
        "include_fields": include_fields,
        "custom_fields": custom_fields,
        "limit": limit,
        "cursor": cursor,
    }
    
    # Remove None values
    params = {k: v for k, v in params.items() if v is not None}

    # Make the request
    response = requests.get(BASE_URL, headers=headers, params=params)

    if response.status_code != 200:
        raise Exception(f"Error {response.status_code}: {response.text}")

    structured_response = response.json()

    # Example: Collect all persons belonging to a specific owner_id
    required_persons_name = []

    for persons in structured_response['data']:
        person_details = {}
        if persons['owner_id'] == owner_id:
            person_details['id'] = persons['id']
            person_details['person_name'] = persons['name']
            required_persons_name.append(person_details)
    
    return required_persons_name


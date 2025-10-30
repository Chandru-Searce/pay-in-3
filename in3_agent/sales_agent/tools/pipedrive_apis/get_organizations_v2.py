# Import necessary packages
import os
import json
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Get the API key from env variables
PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")

BASE_URL = "https://api.pipedrive.com/v1/organizations"

OWNER_ID = int(os.getenv("OWNER_ID_CHANDRU"))

def get_organizations_v2(api_token: str = PIPEDRIVE_API_KEY,
                         filter_id: int = None,
                         ids: str = None,
                         owner_id: int = None,
                         updated_since: str = None,
                         updated_until: str = None,
                         include_fields: str = None,
                         custom_fields: str = None,
                         limit: int = 50,
                         cursor: str = None):
    """
    Fetch organizations from Pipedrive API (v1).
    Optional filters include filter_id, ids, owner_id, updated_since, updated_until, etc.
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
        "updated_since": updated_since,
        "updated_until": updated_until,
        "include_fields": include_fields,
        "custom_fields": custom_fields,
        "limit": limit,
        "cursor": cursor,
    }
    
    # Remove None values so they don’t break the request
    params = {k: v for k, v in params.items() if v is not None}

    # Make the request
    response = requests.get(BASE_URL, headers=headers, params=params)

    # Getting the needed webshop names according to owner id
    structured_response = json.loads(response.text)

    required_webshop_names = []
    print(structured_response)
    for webshop in structured_response['data']:
        organization_details = {}
        if webshop['owner_id']['id'] == owner_id:
            organization_details['org_id'] = webshop['id']
            organization_details['org_name'] = webshop['name']
            required_webshop_names.append(organization_details)
    
    # Return parsed JSON or raw text if not JSON
    try:
        return required_webshop_names
    except ValueError:
        return required_webshop_names

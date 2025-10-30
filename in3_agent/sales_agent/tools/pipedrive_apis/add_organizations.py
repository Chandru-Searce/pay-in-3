# Import necessary packages
import os
import json
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Get the API key from env variables
PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")

BASE_URL = "https://api.pipedrive.com/api/v2/organizations"

def create_organization_v2(name: str,
                           api_token: str = PIPEDRIVE_API_KEY,
                           owner_id: int = None,
                           add_time: str = None,
                           update_time: str = None,
                           visible_to: int = None,
                           label_ids: list = None,
                           address: dict = None):
    """
    Create a new organization in Pipedrive API (v2).
    
    Required:
        - name (string)
    
    Optional:
        - owner_id (int)
        - add_time (str, e.g. '2023-01-01T12:00:00Z')
        - update_time (str)
        - visible_to (int: 0 = owner only, 1 = owner & followers, 3 = entire company)
        - label_ids (list of int)
        - address (dict: { value, country, admin_area_level_1, etc. })
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Build request body
    payload = {
        "name": name,
        "owner_id": owner_id,
        "add_time": add_time,
        "update_time": update_time,
        "visible_to": visible_to,
        "label_ids": label_ids,
        "address": address
    }

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    # Add api_token as query param
    params = {"api_token": api_token}

    # Make POST request
    response = requests.post(BASE_URL, headers=headers, params=params, data=json.dumps(payload))

    if response.status_code != 200:  # 201 = created
        raise Exception(f"Error {response.status_code}: {response.text}")

    return response.json()

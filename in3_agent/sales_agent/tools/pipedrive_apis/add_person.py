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

def create_person_v2(
    name: str,
    api_token: str = PIPEDRIVE_API_KEY,
    owner_id: int = None,
    org_id: int = None,
    add_time: str = None,
    update_time: str = None,
    # Email fields
    email_value: str = None,
    email_primary: bool = None,
    email_label: str = None,
    # Phone fields
    phone_value: str = None,
    phone_primary: bool = None,
    phone_label: str = None,
    # Other optional fields
    visible_to: int = None,
    label_ids: list = None,
    marketing_status: str = None
):
    """
    Create a new person in Pipedrive API (v2).

    Required:
        - name (string)

    Optional:
        - owner_id (int)
        - org_id (int)
        - add_time (str, e.g. '2023-01-01T12:00:00Z')
        - update_time (str)
        - email_value, email_primary, email_label
        - phone_value, phone_primary, phone_label
        - visible_to (int: 0=owner only, 1=owner & followers, 3=company-wide)
        - label_ids (list of int)
        - marketing_status (str)
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Build request body
    payload = {
        "name": name,
        "owner_id": owner_id,
        "org_id": org_id,
        "add_time": add_time,
        "update_time": update_time,
        "visible_to": visible_to,
        "label_ids": label_ids,
        "marketing_status": marketing_status
    }

    # Add email if provided
    if email_value:
        payload["emails"] = [{
            "value": email_value,
            "primary": email_primary if email_primary is not None else False,
            "label": email_label if email_label else "work"
        }]

    # Add phone if provided
    if phone_value:
        payload["phones"] = [{
            "value": phone_value,
            "primary": phone_primary if phone_primary is not None else False,
            "label": phone_label if phone_label else "mobile"
        }]

    # Remove None values from top-level payload
    payload = {k: v for k, v in payload.items() if v is not None}

    # Add api_token as query param
    params = {"api_token": api_token}

    # Make POST request
    response = requests.post(BASE_URL, headers=headers, params=params, data=json.dumps(payload))

    if response.status_code != 200:  # 201 = Created
        raise Exception(f"Error {response.status_code}: {response.text}")

    return response.json()

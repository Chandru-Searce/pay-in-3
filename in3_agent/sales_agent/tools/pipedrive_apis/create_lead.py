# Import necessary packages
import os
import json
import requests
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Get the API key from env variables
PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")

BASE_URL = "https://api.pipedrive.com/v1/leads"

def create_lead(
    title: str,
    api_token: str = PIPEDRIVE_API_KEY,
    owner_id: int = None,
    label_ids: list = None,
    person_id: int = None,
    organization_id: int = None,
    value_amount: float = None,
    value_currency: str = None,
    expected_close_date: str = None,
    visible_to: str = None,
    was_seen: bool = None,
    channel: int = None,
    channel_id: str = None
):
    """
    Create a new lead in Pipedrive API (v1).

    Required:
        - title (string)

    Optional:
        - owner_id (int)
        - label_ids (list of UUIDs)
        - person_id (int)
        - organization_id (int)
        - value_amount (float)
        - value_currency (str, e.g. "USD", "EUR")
        - expected_close_date (str, YYYY-MM-DD)
        - visible_to (str)
        - was_seen (bool)
        - channel (int)
        - channel_id (str)
    """

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    # Build payload
    payload = {
        "title": title,
        "owner_id": owner_id,
        "label_ids": label_ids,
        "person_id": person_id,
        "organization_id": organization_id,
        "expected_close_date": expected_close_date,
        "visible_to": visible_to,
        "was_seen": was_seen,
        "channel": channel,
        "channel_id": channel_id,
    }

    # Handle nested value object
    if value_amount is not None and value_currency:
        payload["value"] = {
            "amount": value_amount,
            "currency": value_currency
        }

    # Remove None values
    payload = {k: v for k, v in payload.items() if v is not None}

    # Add api_token as query param
    params = {"api_token": api_token}

    # Make POST request
    response = requests.post(BASE_URL, headers=headers, params=params, data=json.dumps(payload))
    print(response.status_code)
    if response.status_code != 201:  # 201 = Created
        raise Exception(f"Error {response.status_code}: {response.text}")

    return response.json()


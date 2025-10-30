import os
import json
import requests
from dotenv import load_dotenv
from loguru import logger
from .pipedrive_apis.get_organizations_v2 import get_organizations_v2
from .pipedrive_apis.add_organizations import create_organization_v2
from .pipedrive_apis.add_person import create_person_v2
from .pipedrive_apis.create_lead import create_lead
from .pipedrive_apis.get_persons_v2 import get_persons_v2


# ---------------------------
# Setup loguru logger
# ---------------------------
LOG_FOLDER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "logs")
os.makedirs(LOG_FOLDER_PATH, exist_ok=True)

LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "pipedrive_lead_import.log")
logger.add(LOG_FILE_PATH, rotation="1 MB", retention="7 days", level="INFO")

# Load env variables
load_dotenv()

PIPEDRIVE_API_KEY = os.getenv("PIPEDRIVE_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID_CHANDRU"))


def get_existing_leads():
    """Fetch existing leads from Pipedrive API"""
    url = "https://api.pipedrive.com/v1/leads"
    params = {"api_token": PIPEDRIVE_API_KEY}
    resp = requests.get(url, params=params)
    if resp.status_code != 200:
        logger.error(f"Error fetching leads: {resp.text}")
        raise Exception(f"Error fetching leads: {resp.text}")
    data = resp.json()
    return data["data"] if data and "data" in data else []


def is_duplicate_lead(title, org_id, person_id, existing_leads):
    """Check if a lead already exists"""
    for lead in existing_leads:
        if (
            lead["title"].lower() == title.lower()
            and lead.get("organization_id", None) == org_id
            and lead.get("person_id", None) == person_id
        ):
            return True
    return False


def process_leads(lead_data: dict, max_leads: int = 100):
    """
    Use this tool to push lead data into the Pipedrive CRM system.

    Args:
        lead_data (dict): Lead data (should contain "contacts" key)
        max_leads (int, optional): Limit number of leads to process
    """
    # Fetch existing organizations and persons
    existed_organizations = get_organizations_v2(owner_id=int(OWNER_ID))
    existing_org_map = {org["org_name"]: org["org_id"] for org in existed_organizations}

    existed_persons = get_persons_v2(owner_id=int(OWNER_ID))
    existing_person_map = {p["person_name"]: p["id"] for p in existed_persons}

    existing_leads = get_existing_leads()

    for idx, lead in enumerate(lead_data.get("contacts", [])):
        if max_leads and idx >= max_leads:
            logger.info(f"Reached processing limit of {max_leads} leads, stopping.")
            break

        # Extract and validate fields
        org_name = lead.get("organization_name") or "unknown_organization"
        person_name = lead.get("person_name") or "unknown_person"
        person_email = lead.get("person_email") or None
        person_phone = lead.get("person_phone") or None
        lead_title = lead.get("lead_title") or "unknown_lead"

        # Step 1: Ensure organization exists
        if org_name not in existing_org_map:
            logger.info(f"Creating new organization: {org_name}")
            org_created = create_organization_v2(
                name=org_name,
                owner_id=int(OWNER_ID),
                visible_to=3
            )
            org_id = org_created["data"]["id"]
            existing_org_map[org_name] = org_id
            logger.success(f"Organization created: {org_name} (ID: {org_id})")
        else:
            org_id = existing_org_map[org_name]
            logger.info(f"Organization already exists: {org_name} (ID: {org_id})")

        # Step 2: Ensure person exists
        if person_name not in existing_person_map:
            logger.info(f"Creating new person: {person_name}")
            person_created = create_person_v2(
                name=person_name,
                owner_id=int(OWNER_ID),
                org_id=org_id,
                email_value=person_email,
                email_primary=True,
                phone_value=person_phone,
                phone_primary=True,
                visible_to=3
            )
            person_id = person_created["data"]["id"]
            existing_person_map[person_name] = person_id
            logger.success(f"Person created: {person_name} (ID: {person_id})")
        else:
            person_id = existing_person_map[person_name]
            logger.info(f"Person already exists: {person_name} (ID: {person_id})")

        # Step 3: Ensure lead doesn’t exist
        if is_duplicate_lead(lead_title, org_id, person_id, existing_leads):
            logger.warning(f"Duplicate lead found. Skipping: {lead_title}")
            continue

        # Step 4: Create lead
        logger.info(f"Creating lead: {lead_title}")
        lead_created = create_lead(
            title=lead_title,
            owner_id=int(OWNER_ID),
            person_id=person_id,
            organization_id=org_id,
            visible_to="3"
        )
        logger.success(f"Lead created: {lead_created['data']['id']}")


if __name__ == "__main__":
    # Example: Load the lead_data.json and process 5 leads
    LEAD_DATA_FILE_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "lead_data",
        "contacts.json"
    )

    with open(LEAD_DATA_FILE_PATH, "r") as file:
        lead_data = json.load(file)

    process_leads(lead_data, max_leads=5)

# data = get_existing_leads()
# print(data)
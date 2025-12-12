import requests
import subprocess
import json

# === CONFIGURATION ===
PROJECT_ID = "prj-in3-prod-svc-01"
APP_ID = "in3-prod_1754471936596"
LOCATION = "eu"
AGENT_ID = "4641900726059664395"

DISPLAY_NAME = "Sales Agent"
DESCRIPTION = (
    "A professional B2B Sales Agent that helps you generate qualified leads by"
    "identifying relevant webshops or businesses, extracting decision-maker contact"
    "details, and pushing them directly into your Pipedrive CRM. The agent ensures clean,"
    "structured data, polite communication, and focuses only on valid, business-relevant industries."
)
TOOL_DESCRIPTION = (
    "You are a specialized B2B sales automation agent designed to "
    "handle the entire lead generation workflow. You interpret user "
    "requests for specific business types or webshops, verify compliance"
    " with industry restrictions, retrieve relevant webshop URLs, extract key "
    "contact information of decision-makers (e.g., owners, CEOs, sales directors), "
    "and automatically push all gathered leads into Pipedrive CRM. "
    "You must present sample results in markdown tables with exactly 5 entries "
    "and guide the user through each step politely and professionally. "
    "Do not process prohibited industries such as gambling, finance, adult content, or personal services."
)
REASONING_ENGINE_LOCATION = "europe-west1"
ADK_DEPLOYMENT_ID = "4287479621814845440"

# === GET ACCESS TOKEN ===
access_token = subprocess.check_output(
    ["gcloud", "auth", "print-access-token"], text=True
).strip()

# === HEADERS ===
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
    "X-Goog-User-Project": PROJECT_ID,
}

# === PAYLOAD ===
payload = {
    "displayName": DISPLAY_NAME,
    "description": DESCRIPTION,
    "adk_agent_definition": {
        "tool_settings": {"tool_description": TOOL_DESCRIPTION},
        "provisioned_reasoning_engine": {
            "reasoning_engine": (
                f"projects/{PROJECT_ID}/locations/{REASONING_ENGINE_LOCATION}/"
                f"reasoningEngines/{ADK_DEPLOYMENT_ID}"
            )
        },
    },
}

# === CORRECT PATCH URL ===
url = (
    f"https://eu-discoveryengine.googleapis.com/v1alpha/projects/{PROJECT_ID}"
    f"/locations/{LOCATION}/collections/default_collection/engines/{APP_ID}"
    f"/assistants/default_assistant/agents/{AGENT_ID}"
)

# === MAKE PATCH REQUEST ===
response = requests.patch(url, headers=headers, data=json.dumps(payload))

# === PRINT RESULTS ===
print("Status Code:", response.status_code)
print("Response Body:", response.text)

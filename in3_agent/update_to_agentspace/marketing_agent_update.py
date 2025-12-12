import requests
import subprocess
import json

# === CONFIGURATION ===
PROJECT_ID = "prj-in3-prod-svc-01"
APP_ID = "in3-prod_1754471936596"
LOCATION = "eu"
AGENT_ID = "5421019425764371761"

DISPLAY_NAME = "Marketing Agent"
DESCRIPTION = (
    "A smart Marketing Agent that analyzes your requests and routes them "
    "to the most suitable specialized creative agent — such as Ad Campaign, "
    "Icon, Illustration, Video, or LinkedIn agents. It ensures your request "
    "is handled by the right expert for ads, visuals, videos, or professional posts."
)
TOOL_DESCRIPTION = (
    "You are a professional routing agent responsible for interpreting user "
    "marketing requests and delegating them to the correct specialized agent. "
    "Analyze each request carefully to determine whether it involves ad campaigns, "
    "icons, illustrations, videos, or LinkedIn posts. If the intent is unclear, "
    "ask one concise clarification question before routing. Never create or design "
    "content yourself — your sole purpose is to ensure the request is classified "  
    "and sent to the right downstream agent."
)
REASONING_ENGINE_LOCATION = "europe-west1"
ADK_DEPLOYMENT_ID = "1792098400158613504"

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

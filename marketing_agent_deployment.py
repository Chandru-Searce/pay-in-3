import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from in3_agent.marketing_agent.agent import root_agent

PROJECT_ID = "prj-in3-prod-svc-01"
LOCATION = "europe-west1"
STAGING_BUCKET = "gs://prj-in3-prod-svc-01-bucket-marketing-agent-europe-west1"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

def deploy_marketing_agent():
    remote_app = agent_engines.create(
        display_name="Marketing Agent",
        agent_engine=app,
        requirements= "/home/chandru/Chandru/in3/in3_agent/requirements.txt",
        extra_packages=["./in3_agent/marketing_agent"],
        service_account="sa-vm-gcs-sa-vm-gcs@prj-in3-prod-svc-01.iam.gserviceaccount.com",

    )

def update_marketing_agent():
    remote_app = agent_engines.update(
        display_name="Marketing Agent",
        resource_name="projects/1703329768/locations/europe-west1/reasoningEngines/1792098400158613504",
        agent_engine=app,
        requirements="/home/chandru/Chandru/in3/in3_agent/requirements.txt",
        extra_packages=["./in3_agent/marketing_agent"],
        service_account="sa-vm-gcs-sa-vm-gcs@prj-in3-prod-svc-01.iam.gserviceaccount.com",
    )


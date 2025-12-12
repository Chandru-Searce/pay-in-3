import vertexai
from vertexai import agent_engines
from vertexai.preview import reasoning_engines
from in3_agent.sales_agent.agent import root_agent

PROJECT_ID = "prj-in3-prod-svc-01"
LOCATION = "europe-west1"
STAGING_BUCKET = "gs://prj-in3-prod-svc-01-bucket-sales-agent-europe-west1"

vertexai.init(
    project=PROJECT_ID,
    location=LOCATION,
    staging_bucket=STAGING_BUCKET,
)

app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)


def deploy_sales_agent():
    remote_app = agent_engines.create(
        display_name="Sales Agent",
        agent_engine=app,
        requirements= "/home/chandru/Chandru/in3/in3_agent/requirements.txt",
        extra_packages=["./in3_agent/sales_agent"],
        service_account="sa-vm-gcs-sa-vm-gcs@prj-in3-prod-svc-01.iam.gserviceaccount.com",
        env_vars = {
        # Environment variables for Custom Search API
        "CUSTOM_SEARCH_API": "AIzaSyBhOEdWr-vJV3CAix4Ai1IF_jmGWcg_R9s",
        "CSE_ID": "b2826dd48264a4398",

        # Pipedrive account API token
        "PIPEDRIVE_API_KEY": "584a0b7aa2bf05aac5a310e0800a8f1fe5442eba",
        "OWNER_ID_CHANDRU": "26097507",
        "OWNER_ID_YASH": "26164398",
        "OWNER_ID_TOMMY": "26096781",

        # Apollo API Key
        "APOLLO_API_KEY2": "6Ui1RTLu3gmjJg9NnGcFLQ",

        # APO API URLS
        "PEOPLE_SEARCH_API": "https://api.apollo.io/api/v1/mixed_people/search",
        "PEOPLE_ENRICHMENT_API": "https://api.apollo.io/api/v1/people/match",
        "PEOPLE_BULK_ENRICHMENT_API": "https://api.apollo.io/api/v1/people/bulk_match",
        "ORGANIZATION_SEARCH_API" : "https://api.apollo.io/api/v1/mixed_companies/search",
        # API Endpoints
        "SEARCH_ORGANIZATION_BASE_URL": "https://api.pipedrive.com/v1/organizations/v2/",

        # Bigquery details
        "TABLE_NAME" : "company",
        "BIGQUERY_DATASET" : "in3_snowflake_db_in3_data_model",
        "GCS_BUCKET_NAME": "sales_agent_artifacts"
    })

def update_sales_agent():
    remote_app = agent_engines.update(
        display_name="Sales Agent",
        agent_engine=app,
        requirements="/home/chandru/Chandru/in3/in3_agent/requirements.txt",
        extra_packages=["./in3_agent/sales_agent"],
        service_account="sa-vm-gcs-sa-vm-gcs@prj-in3-prod-svc-01.iam.gserviceaccount.com",
        resource_name="projects/1703329768/locations/europe-west1/reasoningEngines/4287479621814845440",
        env_vars={
            # Environment variables for Custom Search API
            "CUSTOM_SEARCH_API": "AIzaSyBhOEdWr-vJV3CAix4Ai1IF_jmGWcg_R9s",
            "CSE_ID": "b2826dd48264a4398",
            # Pipedrive account API token
            "PIPEDRIVE_API_KEY": "584a0b7aa2bf05aac5a310e0800a8f1fe5442eba",
            "OWNER_ID_CHANDRU": "26097507",
            "OWNER_ID_YASH": "26164398",
            "OWNER_ID_TOMMY": "26096781",
            # Apollo API Key
            "APOLLO_API_KEY2": "6Ui1RTLu3gmjJg9NnGcFLQ",
            # APO API URLS
            "PEOPLE_SEARCH_API": "https://api.apollo.io/api/v1/mixed_people/search",
            "PEOPLE_ENRICHMENT_API": "https://api.apollo.io/api/v1/people/match",
            "PEOPLE_BULK_ENRICHMENT_API": "https://api.apollo.io/api/v1/people/bulk_match",
            "ORGANIZATION_SEARCH_API": "https://api.apollo.io/api/v1/mixed_companies/search",
            # API Endpoints
            "SEARCH_ORGANIZATION_BASE_URL": "https://api.pipedrive.com/v1/organizations/v2/",
            # Bigquery details
            "TABLE_NAME": "company",
            "BIGQUERY_DATASET": "in3_snowflake_db_in3_data_model",
            "GCS_BUCKET_NAME": "sales_agent_artifacts",
        },
    )


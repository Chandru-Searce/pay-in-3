# Import packages
from google.genai import Client

veo_client = Client(
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="us-central1",
)
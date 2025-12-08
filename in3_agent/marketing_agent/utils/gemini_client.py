# Import necassary packages
from google import genai
from google.genai.types import HttpOptions

gemini_client = genai.Client(
    http_options=HttpOptions(api_version="v1"),
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="europe-west4",
)

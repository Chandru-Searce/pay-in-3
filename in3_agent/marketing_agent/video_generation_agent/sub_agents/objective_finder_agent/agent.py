# Import necassary packages
from google.adk.agents import LlmAgent
from .prompt import OBJECTIVE_FINDER_AGENT_PROMPT
from google.genai.types import GenerateContentConfig

root_agent = LlmAgent(
    name="objective_finder_agent",
    description="""
    Responsible for gathering and structuring the initial campaign requirements from the client. 
    The agent interacts with the user to collect key inputs — including campaign objective, target audience, tone, and ad duration — ensuring all essential details are captured accurately for downstream agents. 
    If tone or duration are not specified, it applies default values (tone: “energetic, vibrant, friendly”; ad_duration_seconds: 60). 
    The output is returned in a clean, structured format optimized for subsequent script generation and brand alignment tasks.
    """,
    instruction=OBJECTIVE_FINDER_AGENT_PROMPT,
    model="gemini-2.5-flash",
    generate_content_config=GenerateContentConfig(temperature=0.2, top_k=2, top_p=1.0)
)

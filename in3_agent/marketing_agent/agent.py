# Import necassary packages
from .icon_agent import icon_agent
from google.adk.agents import LlmAgent
from .prompt import MARKETING_AGENT_PROMPT
from .linkedin_agent import linkedin_post_agent
from .ad_campaign_agent import ad_campaign_agent
from .illustration_agent import illustration_agent
from google.genai.types import GenerateContentConfig
from .video_generation_agent import video_generation_agent

root_agent = LlmAgent(
    name="marketing_agent",
    description=""""
    Handles classification of user requests related to content generation. 
    Routes tasks to Imagen Agent for static visuals (images, posts, logos, icons) and to Videogen Agent 
    for dynamic visuals (video ads, animations). Asks a short clarification if the request is ambiguous.
    """,
    instruction=MARKETING_AGENT_PROMPT,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(temperature=0.2, top_k=2, top_p=1.0),
    sub_agents=[
        ad_campaign_agent,
        icon_agent,
        illustration_agent,
        linkedin_post_agent,
        video_generation_agent,
    ],
)

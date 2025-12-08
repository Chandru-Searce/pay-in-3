# Import necassary packages
from google.adk.agents import LlmAgent
from .prompt import ADD_CAMPAIGN_AGENT_PROMPT
from google.genai.types import GenerateContentConfig
from .tools.ad_campaign_editor import _edit_ad_campaign_post
from .tools.ad_campaign_generator import _ad_campaign_generator_function

root_agent = LlmAgent(
    name="ad_campaign_agent",
    description="""
    Handles generation of ad campaign images. Collects key inputs from the user such as core marketing message,
    unique value proposition, and call-to-action button text, then builds an enhanced prompt for image generation. 
    Ensures the final prompt incorporates aesthetic style, logo placement, and icon positioning based on uploaded 
    reference images to produce polished, persuasive ad visuals.
    """,
    instruction=ADD_CAMPAIGN_AGENT_PROMPT,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(temperature=0.2, top_k=2, top_p=1.0),
    tools=[_ad_campaign_generator_function, _edit_ad_campaign_post],
)

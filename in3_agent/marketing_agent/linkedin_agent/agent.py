# Import necassary packages
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig
from .prompt import LINKEDIN_POST_AGENT_PROMPT
from .tools.linkedin_post_generator import _linkedin_post_generator_function
from .tools.linkedin_post_editor import _edit_linkedin_post
from .callbacks.return_artifacts import _return_generated_illustrations

root_agent = LlmAgent(
    name="linkedin_agent",
    description="""
    Handles generation of high-quality LinkedIn posts. Prompts the user for the core content or message to share, 
    and optionally for any visuals to include. Builds an enhanced prompt for post creation that draws on the 
    style, theme, and color palette from uploaded reference images to ensure cohesion, professional tone, and 
    stylistic consistency. Produces polished, engaging text and visuals optimized for LinkedIn audiences, 
    while allowing innovative layouts and phrasing that remain aligned with the reference theme.
    """,
    instruction=LINKEDIN_POST_AGENT_PROMPT,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        top_k=2,
        top_p=1.0
    ),
    tools=[_linkedin_post_generator_function, _edit_linkedin_post],
    after_tool_callback=_return_generated_illustrations
)
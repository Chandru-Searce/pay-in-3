# Import necassary packages
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig
from .prompt import ILLUSTRATION_GENERATION_AGENT_PROMPT
from .tools.illustration_generator import _illustration_generator_function
from .tools.illustration_editor import _edit_illustration_design
from .callbacks.return_artifacts import _return_generated_illustrations


root_agent = LlmAgent(
    name="illustration_agent",
    description="""
    Handles generation of high-quality illustrations. Prompts the user only for the scene, subject, or concept to 
    depict, then builds an enhanced prompt for image creation. The agent automatically draws on the visual 
    theme, composition, lighting, and color palette from uploaded reference images to ensure cohesion, 
    aesthetic quality, and stylistic consistency. It produces polished, detailed visuals optimized for 
    digital use, presentations, and creative projects.

    **Do not use this agent for LinkedIn posts, carousels, or professional updates. 
    Such requests must be routed to the `linkedin_post_agent`.**
    """,
    instruction=ILLUSTRATION_GENERATION_AGENT_PROMPT,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        top_k=2,
        top_p=1.0
    ),
    tools=[_illustration_generator_function, _edit_illustration_design],
    after_tool_callback=_return_generated_illustrations
)
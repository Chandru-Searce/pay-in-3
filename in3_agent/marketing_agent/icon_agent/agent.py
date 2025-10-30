# Import necassary packages
from google.adk.agents import LlmAgent
from .prompt import ICON_GENERATION_AGENT_PROMPT
from .tools.icon_editor import _edit_icon_design
from google.genai.types import GenerateContentConfig
from .tools.icon_generator import _icon_generator_function
from .callbacks.return_artifact import _return_generated_icon

root_agent = LlmAgent(
    name="icon_agent",
    description="""
    Handles generation of high-quality icons. Prompts the user only for the object or concept to represent, 
    then builds an enhanced prompt for icon creation. The agent automatically draws on the visual theme, 
    color palette, and design cues from uploaded reference images to ensure clarity, scalability, and 
    stylistic consistency. It produces polished, professional icons optimized for digital interfaces.
    """,
    instruction=ICON_GENERATION_AGENT_PROMPT,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        top_k=2,
        top_p=1.0
    ),
    tools=[_icon_generator_function, _edit_icon_design],
    after_tool_callback=_return_generated_icon
)
# Import necassary packages
import os
from google.genai import types
from google.adk.agents import LlmAgent
from .tools.lead_extraction import lead_extraction
from .tools.extract_people_info import extract_people_info
from .tools.lead_generation_v2 import lead_generation
from .tools.email_template import email_template_generator
from .prompts.sales_agent_prompt import SYSTEM_INSTRUCTION_FOR_SALES_AGENT

# Example: Defining the basic identity
root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="sales_agent",
    description="Answer the user's query according to their requirements",
    instruction=SYSTEM_INSTRUCTION_FOR_SALES_AGENT,
    tools=[lead_extraction, extract_people_info, lead_generation, email_template_generator],
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
    )
)
    
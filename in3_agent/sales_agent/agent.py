# Import necassary packages
import os
from google.genai import types
from google.adk.agents import LlmAgent
from .tools.apply_filters import _lead_extraction
from .tools.lead_generation_v2 import _lead_generation
from .prompt import SYSTEM_INSTRUCTION_FOR_SALES_AGENT

# Example: Defining the basic identity
root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="sales_agent",
    description="Answer the user's query according to their requirements",
    instruction=SYSTEM_INSTRUCTION_FOR_SALES_AGENT,
    tools=[_lead_extraction, _lead_generation],
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
    )
)
    
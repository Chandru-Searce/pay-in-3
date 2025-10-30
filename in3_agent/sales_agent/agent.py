# Import necassary packages
import os
from google.genai import types
from google.adk.agents import LlmAgent
from .tools.extract_contact_info import extract_contacts
from .tools.extract_webshop_urls import get_webshop_urls
from .tools.lead_generation_v2 import process_leads

# SYSTEM_INSTRUCTION_FILE_PATH
SYSTEM_INSTRUCTION_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),"prompts", "system_instruction_for_sales_agent_v3.txt")

# Load the SYSTEM INSTRUCTION for Sales agent
with open(SYSTEM_INSTRUCTION_FILE_PATH, "r") as file:
    SYSTEM_INSTRUCTION_FOR_SALES_AGENT = file.read()

# Example: Defining the basic identity
root_agent = LlmAgent(
    model="gemini-2.5-pro",
    name="sales_agent",
    description="Answer the user's query according to their requirements",
    instruction=SYSTEM_INSTRUCTION_FOR_SALES_AGENT,
    tools=[get_webshop_urls, extract_contacts, process_leads],
    generate_content_config = types.GenerateContentConfig(
        temperature=0.2,
    )
)
    
# Import necassary packages
from .utils.gemini_client import gemini_client
from google.genai.types import GoogleSearch, Tool, GenerateContentConfig
from ..prompt import SYSTEM_INSTRUCTION_FOR_EMAIL_TEMPLATE_GENERATION

# Initialize client
gemini_client = gemini_client

def _email_template_generator(user_input: str):
    """
    Generates a professional outreach email template introducing the in3 payment solution.

    The function internally initializes a grounding tool (Google Search) and 
    includes it in the generation pipeline. The model response is then returned 
    as plain text.

    Args:
        user_input (str):
            A text input containing any additional instructions, context, or 
            customizations the user wants applied to the generated email template.

    Returns:
        str:
            The generated email template as plain text, formatted and ready for use.
    """

    grounding_tool = Tool(
        google_search= GoogleSearch()
    )

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents=user_input,
        config=GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION_FOR_EMAIL_TEMPLATE_GENERATION,
            temperature=0.2,
            seed=42,
            tools= [grounding_tool]
        )
    )

    return response.text

# Import necassary packages
from .utils.gemini_client import gemini_client
from google.genai.types import GoogleSearch, Tool, GenerateContentConfig
from ..prompts.email_template_prompt import SYSTEM_INSTRUCTION_FOR_EMAIL_TEMPLATE_GENERATION

# Initialize client
gemini_client = gemini_client

def email_template_generator(
        person_name: str,
        person_designation_title: str,
        organization_name: str,
        subject_line: str
):
    """
    Generates a professional outreach email template introducing the in3 payment solution.

    This function uses the provided recipient details to create a clear, concise,
    and ready-to-send email. The generated template introduces in3, explains how it works
    (three interest-free payments, instant approval, zero risk for the webshop), and
    connects the value of in3 to the recipient's organization and role.

    Args:
        person_name (str):
            The full name of the person receiving the email.
        person_designation_title (str):
            The recipient's job title or professional role (e.g., "E-commerce Manager").
        organization_name (str):
            The name of the company or webshop the recipient represents.
        subject_line (str):
            The email subject line that will be used in the generated outreach message.
            This defines the main theme or value proposition presented to the recipient.

    Returns:
        str:
            A fully formatted outreach email template, including greeting, body content,
            in3 explanation, value alignment, and a call-to-action.
    """

    grounding_tool = Tool(
        google_search= GoogleSearch()
    )

    user_input = f"""
    Generate an email template with the following details:

    Recipient Name: {person_name}
    Recipient Title: {person_designation_title}
    Recipient Organization: {organization_name}
    Email Subject Line: {subject_line}
    """
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

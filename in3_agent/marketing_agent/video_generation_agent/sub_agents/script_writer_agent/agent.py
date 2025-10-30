# Import necassary packages
from google.adk.agents import LlmAgent
from google.genai.types import GenerateContentConfig
from .tools.script_generator import _script_generator_func


root_agent = LlmAgent(
    name="script_writer_agent",
    description="""
    Responsible for generating the ad campaign script based on the campaign objective and other collected details. 
    The agent receives structured inputs (objective, audience, tone, ad duration) and passes them to the script generation function to create a detailed ad script including scenes, dialogues, visual elements, and transitions. 
    After the script is generated, it informs the user that the script is ready and asks whether to proceed with the ad video generation process.
    """,
    instruction="""
    The campaign objective and related details will be provided for script generation. 
    Pass these details to the _script_generator_func to generate the full ad script, including scene breakdowns, dialogues, visual elements, and transitions. 
    Once the script is generated, inform the user that the script is ready and ask: "The ad script has been successfully generated. Shall we proceed with the ad video generation process?"
    Ensure all communication is concise, professional, and clear.
    """,
    model="gemini-2.5-pro",
    generate_content_config=GenerateContentConfig(
        temperature=0.2,
        top_k=2,
        top_p=1.0
    ),
    tools=[_script_generator_func]
)
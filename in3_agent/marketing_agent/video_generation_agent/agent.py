# Import all necassary pacakges
from google.adk.agents import LlmAgent
from .prompt import VIDEO_GENERATION_AGENT_PROMPT
from google.genai.types import GenerateContentConfig
from .tools.video_generation import video_generation_func
from .sub_agents.script_writer_agent import script_writer_agent
from .sub_agents.objective_finder_agent import objective_finder_agent

root_agent = LlmAgent(
    name="video_agent",
    description="""
    Orchestrates the full ad campaign video generation process. 
    Manages the Objective Finder, Script Writer and Initial frame generator agents, 
    passing outputs step by step to ensure alignment with the in3 brand guidelines. 
    Generates final videos by calling `video_generation_func(scene_script)` sequentially, 
    ensuring smooth scene transitions, stylistic consistency, and cohesive storytelling 
    across the entire campaign.
    """,
    instruction=VIDEO_GENERATION_AGENT_PROMPT,
    model="gemini-2.5-flash",
    generate_content_config=GenerateContentConfig(temperature=0.2, top_k=2, top_p=1.0),
    sub_agents=[objective_finder_agent, script_writer_agent],
    tools=[video_generation_func],
)

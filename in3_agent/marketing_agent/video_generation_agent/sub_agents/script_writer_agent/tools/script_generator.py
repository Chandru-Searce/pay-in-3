# Import necassary packages
import os
from typing import List
from google import genai
from .prompt import SCRIPT_GENERATOR_PROMPT
from pydantic import BaseModel, Field, ValidationError
from google.genai.types import GenerateContentConfig, Content, Part

# Output JSON file for the ad video script
VIDEO_SCRIPT_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "ad_script", "ad_video_script.json"
)

# Pydantic Structure
class Shot(BaseModel):
    shot_number: int = Field(..., description="Sequential number of the shot")
    timestamp: str = Field(..., description="Time range of the shot, e.g., '0s–3s'")
    subject: str = Field(..., description="Characters and key objects in flat 2D brand style")
    action: str = Field(..., description="What the subject is doing, include motion style and easing")
    style: str = Field(..., description="Flat 2.5D vector illustration, Alegria or Corporate Memphis")
    camera_positioning_and_motion: str = Field(..., description="Camera movement description")
    composition: str = Field(..., description="Framing and layout description")
    focus_and_lens_effects: str = Field(..., description="Lens/focus effects; use Soft Aqua Marine glow only for key highlights")
    ambiance: str = Field(..., description="Mood using brand colors (Gulf Blue, Lovely Purple, Aqua Marine, etc.)")
    enhance_facial_details: str = Field(..., description="Character expression focus")
    dialogue: str = Field(..., description="VO")
    sound_effects: str = Field(..., description="Subtle UI/interaction sounds")
    ambient_noise: str = Field(..., description="Environmental sounds")

class Scene(BaseModel):
    scene_number: int = Field(..., description="Sequential number of the scene")
    scene_title: str = Field(..., description="Title describing the scene")
    scene_duration: str = Field(..., description="Duration of the scene, e.g., '0s–8s'")
    shots: List[Shot] = Field(..., description="List of shots within the scene")

class VideoScript(BaseModel):
    scenes: List[Scene] = Field(..., description="List of scenes in the video script")


# Gemini Client Initialization
gemini_client = genai.Client(
    vertexai=True,
    project="prj-in3-non-prod-svc-01",
    location="europe-west4",
)


# Script Generation Function
def _script_generator_func(
    ad_campaign_objective: str,
    output_file: str = VIDEO_SCRIPT_FILE
):
    """
    Generate ad video script JSON from user objective, validate with Pydantic,
    and save to a JSON file.
    """
    user_objective = Content(
        role="user",
        parts=[Part(text=ad_campaign_objective)]
    )

    # Generate script using Gemini model
    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        config=GenerateContentConfig(
            system_instruction=SCRIPT_GENERATOR_PROMPT,
            temperature=1,
            response_schema=VideoScript.model_json_schema(),
            response_mime_type="application/json"
        ),
        contents=user_objective
    )

    # Parse and validate JSON using Pydantic v2
    try:
        video_script = VideoScript.model_validate_json(response.text)
        print("✅ Video script successfully parsed and validated.")
    except ValidationError as e:
        print("❌ Failed to validate the response JSON:")
        print(e.model_dump_json(indent=2))
        return

    # Save JSON file
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(video_script.model_dump_json(indent=2))

    print(f"✅ Video script saved to {output_file}")

    return {
        "status": "Successfully ad video script has been generated"
    }


# Example Usage
if __name__ == "__main__":
    _script_generator_func(
        ad_campaign_objective="""
Campaign Objective: Showcase in3’s new one-click checkout feature

Target Audience: Tech-savvy millennials and Gen Z online shoppers

Desired Tone: Exciting, modern, playful

Ad Duration: 24 seconds
"""
    )

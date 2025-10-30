# Import necassary packages
from typing import Dict, Any
from google.genai import types
from google.genai.types import Part
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

def _return_generated_ad_campaign_video(
    tool: FunctionTool,
    args: Dict[str, Any],
    tool_response: bytes,
    tool_context: ToolContext,
) -> Part:
    """
    This callback function will be called after video_generation_func ends.
    """
    if tool.name == "video_generation_func":
        # Persist the artifact (you can also write to GCS, S3, etc.)
        artifact = tool_context.save_artifact(
            filename="ad_campaign_video.mp4",
            artifact=tool_response
        )
        
        return artifact


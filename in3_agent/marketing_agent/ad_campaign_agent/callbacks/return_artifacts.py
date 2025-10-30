from typing import Dict, Any, List
from google.genai.types import Part
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

async def after_tool_callback_func(
    tool: FunctionTool,
    args: Dict[str, Any],
    tool_response: List[Part],
    tool_context: ToolContext,
) -> Part:
    """
    Called after ad campaign generator or edit finishes.
    """
    if tool.name in ("_ad_campaign_generator_function", "_edit_ad_campaign_post"):
        # Await the async call

        # Use this if you want return the ad campaign post with text components
        artifact_with_text = await tool_context.save_artifact(
            filename="ad_campaign_image_with_text.png",
            artifact=tool_response[0]
        )

        # Use this if you want to return the ad campaign post without text components
        artifact_without_text = await tool_context.save_artifact(
            filename="ad_campaign_image_without_text.png",
            artifact=tool_response[-1]
        )

        # Saving the last generated image for editing purpose if needed
        tool_context.state['latest_ad_campaign_post'] = tool_response[0]

        return artifact_with_text, artifact_without_text

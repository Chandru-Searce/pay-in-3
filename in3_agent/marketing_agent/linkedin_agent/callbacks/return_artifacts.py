# Import necassary packages
from typing import Dict, Any, List
from google.genai.types import Part
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

async def _return_generated_illustrations(
    tool: FunctionTool,
    args: Dict[str, Any],
    tool_response: List[Part],
    tool_context: ToolContext,
) -> Part:
    """
    This callback function will be called after _linkedin_post_generator_function ends.
    """
    if tool.name in ("_linkedin_post_generator_function", "_edit_linkedin_post"):
        # Persist the artifact (you can also write to GCS, S3, etc.)
        artifact_with_text = await tool_context.save_artifact(
            filename="linkedin_post_generated_with_text.png",
            artifact=tool_response[0]
        )

        artifact_without_text = await tool_context.save_artifact(
            filename="linkedin_post_generated_without_text.png",
            artifact=tool_response[-1]
        )

        tool_context.state['latest_linkedin_post'] = tool_response[0]
        
        return artifact_with_text, artifact_without_text


# Import necassary packages
from typing import Dict, Any
from google.genai.types import Part
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

async def _return_generated_icon(
    tool: FunctionTool,
    args: Dict[str, Any],
    tool_response: Dict,
    tool_context: ToolContext,
) -> Part:
    """
    This callback function will be called after _icon_generator_function ends.
    """
    if tool.name in ("_icon_generator_function", "_edit_icon_design"):

        # Save the artifact
        artifact = await tool_context.save_artifact(
            filename="icon_generated.png",
            artifact=tool_response
        )

        tool_context.state['latest_icon_generated'] = tool_response
        
        return artifact


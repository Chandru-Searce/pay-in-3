# Import necassary packages
from typing import Dict, Any
from google.genai.types import Part
from google.adk.tools import FunctionTool
from google.adk.tools.tool_context import ToolContext

def _return_generated_illustrations(
    tool: FunctionTool,
    args: Dict[str, Any],
    tool_response: Part,
    tool_context: ToolContext,
) -> Part:
    """
    This callback function will be called after _icon_generator_function ends.
    """
    if tool.name in ("_illustration_generator_function", "_edit_illustration_design"):

        # Save artifacts
        artifact = tool_context.save_artifact(
            filename="illustration_generated.png",
            artifact=tool_response
        )
        
        tool_context.state['latest_illustration'] = tool_response

        return artifact
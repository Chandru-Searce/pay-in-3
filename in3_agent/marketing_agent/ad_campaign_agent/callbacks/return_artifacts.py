import uuid
import datetime
from google.auth import default
from typing import Dict, Any, List
from google.genai.types import Part
from google.adk.tools import FunctionTool
from ...utils.storage_client import storage_client
from google.adk.tools.tool_context import ToolContext

credentials, _ = default()

async def upload_to_gcs(
        image_object: Part,
        destination_blob_name: str,
    ):

    """
    This function helps to store the generate image into gcs bucket
    """

    bucket = storage_client.bucket(
        bucket_name="marketing_agent_artifacts",
    )

    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(
        data=image_object.inline_data.data,
        content_type="image/png"
    )

    gcs_uri = f"gs://marketing_agent_artifacts/{destination_blob_name}"

    return gcs_uri

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

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        blob_name = f"ad_campaigns/{timestamp}_{uuid.uuid4().hex[:8]}_with_text.png"

        gcs_uri = await upload_to_gcs(image_object=tool_response[0], destination_blob_name=blob_name)

        # Saving the last generated image for editing purpose if needed
        tool_context.state['latest_ad_campaign_post'] = gcs_uri

        return artifact_with_text, artifact_without_text

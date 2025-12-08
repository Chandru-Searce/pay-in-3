# Import necassary packages
import uuid
from google.genai import types
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from ...utils.gemini_client import gemini_client
from ...utils.storage_client import storage_client
from ..utils.text_remover import _remove_text_from_generated_image


def _edit_ad_campaign_post(
    user_prompt: str, tool_context: ToolContext, aspect_ratio: str
):
    """
    Use this tool to edit the ad campaign image according to the user's specified changes.

    Parameters
    ----------
    user_prompt : str
        The user's instructions describing the desired changes to the ad campaign image.

    aspect_ratio (str):
        The desired aspect ratio for the generated image.
        Must be one of the following valid ratios:
        - "1:1"   → Square
        - "4:5"   → Portrait
        - "16:9"  → Widescreen

    Returns
    -------
    types.Part
        An object containing the edited ad campaign image in PNG format as `inline_data`.
        If no image was generated, returns a string: "No image was generated."
    """
    bucket_name = "marketing_agent_artifacts"
    bucket = storage_client.bucket(bucket_name=bucket_name)

    latest_ad_campaign_post_uri = tool_context.state.get(
        "latest_ad_campaign_post_uri_with_text"
    )

    latest_ad_campaign_post = types.Part.from_uri(
        file_uri=latest_ad_campaign_post_uri, mime_type="image/png"
    )

    # Generate config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.0,
        top_k=1,
        top_p=0.95,
        image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        max_output_tokens=32768,
        response_modalities=["IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(
                category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"
            ),
            types.SafetySetting(
                category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"
            ),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )

    text_input = types.Part.from_text(text=user_prompt)

    contents = [
        types.Content(
            role="user",
            parts=[latest_ad_campaign_post, text_input],
        )
    ]

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
        config=generate_content_config,
        contents=contents,
    )

    # --- Collect first generated image ---
    generated_image = None
    for cand in response.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None):
                generated_image = part.inline_data.data
                break
        if generated_image:
            break

    if not generated_image:
        return "No image was generated."

    # --- Timestamp (timezone-aware, no deprecation warning) ---
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    destination_blob_with_text = (
        f"ad_campaigns/{timestamp}_{uuid.uuid4().hex[:8]}_with_text(edited).png"
    )
    blob_with_text = bucket.blob(destination_blob_with_text)
    blob_with_text.upload_from_string(data=generated_image, content_type="image/png")

    # --- Construct final URIs ---
    with_text_gcs_uri = f"gs://{bucket_name}/{destination_blob_with_text}"

    # --- Generate "without text" image (custom method) ---
    generated_image_without_text = _remove_text_from_generated_image(
        gcs_uri_with_text=with_text_gcs_uri
    )

    # --- Store "without text" image in GCS ---
    destination_blob_without_text = (
        f"ad_campaigns/{timestamp}_{uuid.uuid4().hex[:8]}_without_text(edited).png"
    )
    blob_without_text = bucket.blob(destination_blob_without_text)
    blob_without_text.upload_from_string(
        data=generated_image_without_text, content_type="image/png"
    )

    tool_context.state["latest_ad_campaign_post_uri_with_text"] = with_text_gcs_uri

    # --- Return structured response ---
    return {
        "Status": "Ad campaign image edited successfully",
        "With_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_with_text}",
        "Without_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_without_text}",
    }

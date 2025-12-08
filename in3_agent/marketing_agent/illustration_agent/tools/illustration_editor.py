# Import necassary packages
import uuid
from google.genai import types
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from ...utils.gemini_client import gemini_client
from ...utils.storage_client import storage_client

def _edit_illustration_design(
    user_prompt: str, tool_context: ToolContext, aspect_ratio: str
):
    """
    Use this tool to edit the illustration design according to the user's specified changes.

    Parameters
    ----------
    user_prompt : str
        The user's instructions describing the desired changes to the illustration design.

    aspect_ratio (str):
        The desired aspect ratio for the generated image.
        Must be one of the following valid ratios:
        - "1:1"   → Square
        - "4:3"   → Landscape
        - "4:5"   → Portrait
        - "16:9"  → Widescreen
        - "21:9"  → Ultrawide (Cinematic)

    Returns
    -------
    types.Part
        An object containing the edited illustration design in PNG format as `inline_data`.
        If no image was generated, returns a string: "No image was generated."
    """
    bucket_name = "marketing_agent_artifacts"
    bucket = storage_client.bucket(bucket_name=bucket_name)

    latest_illustration_uri = tool_context.state.get("latest_illustration_uri")

    latest_illustration = types.Part.from_uri(
        file_uri=latest_illustration_uri, mime_type="image/png"
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
            parts=[latest_illustration, text_input],
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

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    destination_blob = f"illustrations/{timestamp}_{uuid.uuid4().hex[:8]}_(edited).png"
    blob = bucket.blob(destination_blob)
    blob.upload_from_string(data=generated_image, content_type="image/png")

    return {
        "Status": "Illustration edited successfully",
        "Edited_Illustration_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob}",
    }

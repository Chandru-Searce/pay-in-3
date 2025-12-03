# Import necassary packages
import uuid
from google import genai
from google.genai import types
from google.cloud.storage import Client
from google.adk.tools import ToolContext
from datetime import datetime, timezone
from ...utils.gemini_client import gemini_client
from ...utils.storage_client import storage_client
from ..utils.text_remover import _remove_text_from_generated_image

# gemini_client = genai.Client(
#         vertexai=True,
#         project="prj-in3-prod-svc-01",
#         location="europe-west4",
#     )

# storage_client = Client(
#     project="prj-in3-prod-svc-01"
# )

def _edit_linkedin_post(user_prompt: str, tool_context: ToolContext, aspect_ratio: str):
    """
    Use this tool to edit the linkedin post according to the user's specified changes.

    Parameters
    ----------
    user_prompt : str
        The user's instructions describing the desired changes to the linkedin post.

    aspect_ratio (str):
        The desired aspect ratio for the generated image.  
        Must be one of the following valid ratios:
        - "1:1"   → Square  
        - "4:5"   → Portrait   
        - "16:9"  → Widescreen 

    Returns
    -------
    types.Part
        An object containing the edited linkedin post in PNG format as `inline_data`.
        If no image was generated, returns a string: "No image was generated."
    """
    bucket_name = "marketing_agent_artifacts"
    bucket = storage_client.bucket(
        bucket_name=bucket_name
    )

    latest_linkedin_post_uri = tool_context.state.get("latest_linkedin_post_uri")

    latest_linkedin_post = types.Part.from_uri(
        file_uri=latest_linkedin_post_uri, mime_type="image/png"
    )
    # Generate config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.0,
        top_k=1,
        top_p=0.95,
        image_config=types.ImageConfig(
            aspect_ratio=aspect_ratio
        ),
        max_output_tokens=32768,
        response_modalities=["IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )
    
    text_input = types.Part.from_text(text=user_prompt)

    contents = [
        types.Content(
            role="user",
            parts=[latest_linkedin_post, text_input],
        )
    ]

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
        config=generate_content_config,
        contents=contents
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
    
    # with open("ad_campaign_image.png", "wb") as f:
    #     f.write(generated_image)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    destination_blob_with_text = f"linkedin_posts/{timestamp}_{uuid.uuid4().hex[:8]}_with_text_(edited).png"
    blob = bucket.blob(destination_blob_with_text)
    
    blob.upload_from_string(
        data=generated_image,
        content_type="image/png"
    )

    linkedin_post_uri_edited_with_text = f"gs://{bucket_name}/{destination_blob_with_text}"

    # edited_image_with_text = types.Part(inline_data=types.Blob(data=generated_image, mime_type="image/png"))

    edited_image_without_text = _remove_text_from_generated_image(gcs_uri_with_text=linkedin_post_uri_edited_with_text)

    destination_blob_without_text = f"linkedin_posts/{timestamp}_{uuid.uuid4().hex[:8]}_without_text_(edited).png"
    blob = bucket.blob(destination_blob_without_text)
    blob.upload_from_string(
        data=edited_image_without_text,
        content_type="image/png"
    )

    tool_context.state['latest_linkedin_post_uri'] = linkedin_post_uri_edited_with_text

    return {
        "Status": "Linkedin post edited successfully",
        "With_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_with_text}",
        "Without_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_without_text}"
    }

    
# Import necassary packages
import uuid
import random
from google import genai
from google.genai import types
from google.cloud import storage
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from google.genai.types import ImageConfig
from ...utils.gemini_client import gemini_client
from ...utils.storage_client import storage_client
from ..utils.text_remover import _remove_text_from_generated_image

# gemini_client = genai.Client(
#         vertexai=True,
#         project="prj-in3-prod-svc-01",
#         location="europe-west4",
#     )

# storage_client = storage.Client(
#         project="prj-in3-prod-svc-01"
#     )

def _get_relevant_images():
    """
    Use this tool to get the relevant images for generating ad campaign posts or visuals.

    Returns:
        List[str]: 
            A list of matching file names (including their full paths within the bucket).
            Returns an empty list if no files are found.
    """
    bucket_name = "in3-brand-guidelines"
    folder = "Brand guidelines /images/"
    starts_with = ['ad']

    results = []
    print(f"Looking for files in '{bucket_name}/{folder}' starting with '{starts_with}'...")

    for prefix in starts_with:
        # Combine folder and the current starting string
        search_prefix = f"{folder.rstrip('/')}/{prefix}"
        blobs = storage_client.list_blobs(bucket_name, prefix=search_prefix)
        for blob in blobs:
            results.append("gs://in3-brand-guidelines/"+blob.name)

    if results:
        selected = random.sample(results, min(len(results), 3))

        print("Selected files:\n")
        for name in selected:
            print(name)
        return selected
    else:
        print("No files found.")
        return []

def _ad_campaign_generator_function(input_text: str, aspect_ratio: str, tool_context: ToolContext): 
    """
    Use this tool to generate ad campaign post/image using the Gemini model.

    Args:
        input_text (str): 
            The enhanced user prompt containing campaign message, CTA, 
            and style/layout instructions.

        aspect_ratio (str):
            The desired aspect ratio for the generated image.  
            Must be one of the following valid ratios:
            - "1:1"   → Square   
            - "4:5"   → Portrait   
            - "16:9"  → Widescreen  

    Returns:
        types.Part: 
            A generated image as types.Part objects.
    """
    # --- Initialize storage ---
    bucket_name = "marketing_agent_artifacts"
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)

    # --- Prepare reference images ---
    reference_images_uri = _get_relevant_images()
    image_parts = []
    for uri in reference_images_uri[:3]:  # Gemini supports up to 3 images
        image_parts.append(
            types.Part.from_uri(file_uri=uri, mime_type="image/png")
        )

    # --- Prepare user text prompt ---
    text_part = types.Part.from_text(text=input_text)

    # --- Combine images and text into request content ---
    contents = [
        types.Content(
            role="user",
            parts=image_parts + [text_part],
        )
    ]

    # --- Configure generation parameters ---
    generate_content_config = types.GenerateContentConfig(
        temperature=0.0,
        top_k=1,
        top_p=0.95,
        image_config=ImageConfig(aspect_ratio=aspect_ratio),
        max_output_tokens=32768,
        response_modalities=["IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )

    # --- Generate content via Gemini ---
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=generate_content_config,
    )

    # --- Extract first generated image ---
    generated_image = None
    for cand in response.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None):
                generated_image = part.inline_data.data
                break
        if generated_image:
            break

    if not generated_image:
        return {"Status": "No image was generated."}

    # --- Timestamp (timezone-aware, no deprecation warning) ---
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")

    # --- Store "with text" image in GCS ---
    destination_blob_with_text = f"ad_campaigns/{timestamp}_{uuid.uuid4().hex[:8]}_with_text.png"
    blob_with_text = bucket.blob(destination_blob_with_text)
    blob_with_text.upload_from_string(
        data=generated_image,
        content_type="image/png"
    )

    # --- Construct final URIs ---
    with_text_gcs_uri = f"gs://{bucket_name}/{destination_blob_with_text}"

    # --- Generate "without text" image (custom method) ---
    generated_image_without_text = _remove_text_from_generated_image(gcs_uri_with_text=with_text_gcs_uri)

    # --- Store "without text" image in GCS ---
    destination_blob_without_text = f"ad_campaigns/{timestamp}_{uuid.uuid4().hex[:8]}_without_text.png"
    blob_without_text = bucket.blob(destination_blob_without_text)
    blob_without_text.upload_from_string(
        data=generated_image_without_text,
        content_type="image/png"
    )

    # --- Update tool context state ---
    tool_context.state["latest_ad_campaign_post_uri_with_text"] = with_text_gcs_uri

    # --- Return structured response ---
    return {
        "Status": "Ad campaign image generation completed successfully",
        "With_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_with_text}",
        "Without_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_without_text}"
    }



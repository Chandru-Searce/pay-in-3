# Import necassary packages
import uuid
import random
from google import genai
from google.genai import types
from google.cloud import storage
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from ...utils.gemini_client import gemini_client
from ...utils.storage_client import storage_client

# gemini_client = genai.Client(
#         vertexai=True,
#         project="prj-in3-prod-svc-01",
#         location="europe-west4",
#     )

# storage_client = storage.Client(
#         project="prj-in3-prod-svc-01"
#     )

def _get_relevant_icon_images():
    """
    Use this tool to get the relevant icon images for generating icons.

    Returns:
        List[str]: 
            A list of matching file names (including their full paths within the bucket).
            Returns an empty list if no files are found.
    """
    bucket_name = "in3-brand-guidelines"
    folder = "Brand guidelines /images/"
    starts_with = ['icon']

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
        for name in selected:
            print(name)
        return selected
    else:
        print("No files found.")
        return []
    
def _icon_generator_function(input_text: str, tool_context: ToolContext): 
    """
    Use this tool to generate icon images using the Gemini model.

    Args:
        input_text (str): 
            The enhanced user prompt containing logo description.
    
    Returns:
        types.Part: 
            A generated image as types.Part objects.
    """
    bucket_name = "marketing_agent_artifacts"
    bucket = storage_client.bucket(
        bucket_name=bucket_name
    )

    # Prepare image parts dynamically based on input list
    reference_images_uri = _get_relevant_icon_images()
    image_parts = []
    for uri in reference_images_uri:
        image_parts.append(
            types.Part.from_uri(file_uri=uri, mime_type="image/png")
        )
        if len(image_parts) == 3:  # We can only pass upto 3 images for gemini-2.5-image-preview
            break

    # Prepare user prompt
    text_part = types.Part.from_text(text=input_text)

    # Model
    model = "gemini-2.5-flash-image"

    # Create content (combine images + text)
    contents = [
        types.Content(
            role="user",
            parts=image_parts + [text_part],
        )
    ]

    # Generate config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.0,
        top_k=1,
        top_p=0.95,
        max_output_tokens=32768,
        response_modalities=["IMAGE"],
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
    )

    # Generate content
    response = gemini_client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config,
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

    # with open("icon_generated.png", "wb") as f:
    #     f.write(generated_image)
        
    # generated_image = types.Part(inline_data=types.Blob(data=generated_image, mime_type="image/png"))

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    destination_blob = f"icons/{timestamp}_{uuid.uuid4().hex[:8]}.png"
    blob = bucket.blob(destination_blob)
    blob.upload_from_string(
        data=generated_image,
        content_type="image/png"
    )

    # --- Construct final URIs ---
    icon_gcs_uri = f"gs://{bucket_name}/{destination_blob}"

    # --- Update tool context state ---
    tool_context.state["latest_icon_generated_uri"] = icon_gcs_uri
    
    # return generated_image

    # --- Return structured response ---
    return {
        "Status": "Icon generation completed successfully",
        "Generated_Icon_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob}",
    }
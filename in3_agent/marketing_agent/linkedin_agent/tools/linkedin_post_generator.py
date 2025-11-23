# Import necassary packages
import uuid
import random
from google import genai
from google.genai import types
from google.cloud import storage
from datetime import datetime, timezone
from google.adk.tools import ToolContext
from ..utils.text_remover import _remove_text_from_generated_image

gemini_client = genai.Client(
        vertexai=True,
        project="prj-in3-prod-svc-01",
        location="europe-west4",
    )

storage_client = storage.Client(
        project="prj-in3-prod-svc-01"
    )

def _get_relevant_linkedin_post_images():
    """
    Use this tool to get the relevant linkedin post images for generating icons.

    Returns:
        List[str]: 
            A list of matching file names (including their full paths within the bucket).
            Returns an empty list if no files are found.
    """

    bucket_name = "in3-brand-guidelines"
    folder = "Brand guidelines /images/"    
    starts_with = ['linkedin']

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
        print("Bucket Name:", bucket_name)
        print("No files found.")
        return []

def _linkedin_post_generator_function(input_text: str, aspect_ratio: str, tool_context: ToolContext): 
    """
    Use this tool to generate linkedin post images using the Gemini model.

    Args:
        input_text (str): 
            The enhanced user prompt containing logo description.

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
    bucket_name = "marketing_agent_artifacts"
    bucket = storage_client.bucket(
        bucket_name=bucket_name
    )

    # Prepare image parts dynamically based on input list
    reference_images_uri = _get_relevant_linkedin_post_images()

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
        image_config = types.ImageConfig(
            aspect_ratio=aspect_ratio
        ),
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

    # with open("linkedin_post_generated.png", "wb") as f:
    #     f.write(generated_image)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    destination_blob_with_text = f"linkedin_posts/{timestamp}_{uuid.uuid4().hex[:8]}_with_text.png"
    blob = bucket.blob(destination_blob_with_text)
    blob.upload_from_string(
        data=generated_image,
        content_type="image/png"
    )

    # --- Construct final URIs ---
    linkedin_post_gcs_uri = f"gs://{bucket_name}/{destination_blob_with_text}"

    # --- Update tool context state ---
    tool_context.state["latest_linkedin_post_uri"] = linkedin_post_gcs_uri

    # generated_image_with_text = types.Part(inline_data=types.Blob(data=generated_image, mime_type="image/png"))
    
    generated_image_without_text = _remove_text_from_generated_image(gcs_uri_with_text=linkedin_post_gcs_uri)
    
    destination_blob_without_text = f"linkedin_posts/{timestamp}_{uuid.uuid4().hex[:8]}_without_text.png"
    blob = bucket.blob(destination_blob_without_text)
    blob.upload_from_string(
        data=generated_image_without_text,
        content_type="image/png"
    )

    # --- Return structured response ---
    return {
        "Status": "Linkedin post generation completed successfully",
        "With_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_with_text}",
        "Without_Text_Public_URL": f"https://storage.cloud.google.com/{bucket_name}/{destination_blob_without_text}"
    }

    # return generated_image_with_text, generated_image_without_text
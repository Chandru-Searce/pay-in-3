# Import necassary packages
import random
from google import genai
from google.cloud import storage
from google.genai import types
from google.genai.types import ImageConfig
from ..utils.text_remover import _remove_text_from_generated_image

gemini_client = genai.Client(
        vertexai=True,
        project="prj-in3-non-prod-svc-01",
        location="europe-west4",
    )

storage_client = storage.Client(
        project="prj-in3-non-prod-svc-01"
    )

def _get_relevant_images():
    """
    Use this tool to get the relevant images for generating ad campaign posts or visuals.

    Returns:
        List[str]: 
            A list of matching file names (including their full paths within the bucket).
            Returns an empty list if no files are found.
    """

    bucket_name = "brand-guidelines-in3"
    folder = "brand_guidelines/images/"
    starts_with = ['ad']

    results = []
    print(f"Looking for files in '{bucket_name}/{folder}' starting with '{starts_with}'...")

    for prefix in starts_with:
        # Combine folder and the current starting string
        search_prefix = f"{folder.rstrip('/')}/{prefix}"
        blobs = storage_client.list_blobs(bucket_name, prefix=search_prefix)
        for blob in blobs:
            results.append("gs://brand-guidelines-in3/"+blob.name)

    if results:
        selected = random.sample(results, min(len(results), 3))

        print("Selected files:\n")
        for name in selected:
            print(name)
        return selected
    else:
        print("No files found.")
        return []

def _ad_campaign_generator_function(input_text: str, aspect_ratio: str): 
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
    # Prepare image parts dynamically based on input list
    reference_images_uri = _get_relevant_images()
    
    image_parts = []
    for uri in reference_images_uri:
        image_parts.append(
            types.Part.from_uri(file_uri=uri, mime_type="image/png")
        )
        if len(image_parts) == 3:  # We can only pass upto 3 images for gemini-2.5-image-preview
            break

    # Prepare user prompt
    text_part = types.Part.from_text(text=input_text)

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
        image_config=ImageConfig(
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

    # Generate content
    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
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

    # with open("ad_campaign_image.png", "wb") as f:
    #     f.write(generated_image)

    generated_image_with_text = types.Part(inline_data=types.Blob(data=generated_image, mime_type="image/png"))

    generated_image_without_text = _remove_text_from_generated_image(generated_image=generated_image_with_text)
    
    return [generated_image_with_text, generated_image_without_text]

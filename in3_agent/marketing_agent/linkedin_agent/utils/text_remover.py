# Import necassary packages
from google.genai import types
from .prompt import TEXT_REMOVER_PROMPT
from ...utils.gemini_client import gemini_client


def _remove_text_from_generated_image(gcs_uri_with_text: str) -> bytes:
    """
    This function helps to remove from the generated image without modifiying other visual elements.

    Args:
        generated_image:
            Generated image which contains headline text and CTA button text.

    Returns:
        types.Part:
            A generated image without text as types.Part objects.
    """

    prompt_for_remove_text = types.Part(text=TEXT_REMOVER_PROMPT)

    generated_image_with_text = types.Part.from_uri(
        file_uri=gcs_uri_with_text, mime_type="image/png"
    )

    content = [
        types.Content(
            role="user", parts=[generated_image_with_text] + [prompt_for_remove_text]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature=0.0,
        seed=42,
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

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=content,
        config=generate_content_config,
    )

    # --- Collect first generated image ---
    generated_image_without_text = None
    for cand in response.candidates:
        for part in cand.content.parts:
            if getattr(part, "inline_data", None):
                generated_image_without_text = part.inline_data.data
                break
        if generated_image_without_text:
            break

    if not generated_image_without_text:
        return "No image was generated."

    return generated_image_without_text

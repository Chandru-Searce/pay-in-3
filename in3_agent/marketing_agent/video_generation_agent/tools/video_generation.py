# Import necassary packages
import os
import cv2
import json
import time
import uuid
import tempfile
from google.genai import Client
from google.cloud import storage
from google.genai import types
from datetime import datetime, timezone
from .prompt import INITIAL_FRAME_GENERATION_PROMPT
from moviepy import VideoFileClip, concatenate_videoclips
from google.genai.types import VideoGenerationReferenceImage, VideoGenerationReferenceType

gemini_client = Client(
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="europe-west4",
)

veo_client = Client(
    vertexai=True,
    project="prj-in3-prod-svc-01",
    location="us-central1",
)

storage_client = storage.Client(
    project="prj-in3-prod-svc-01"
)

def _generate_prompt_for_initial_frame():
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sub_agents", "script_writer_agent", "ad_script", "ad_video_script.json")

    with open(script_path, "r", encoding="utf-8") as f:
        video_script = json.load(f)  # use json.load, not json.loads

    initial_scene = video_script['scenes'][0]

    response = gemini_client.models.generate_content(
        model="gemini-2.5-pro",
        contents= types.Content(
            role="user",
            parts=[
                types.Part(
                    text= "Here is the initial scene\n\n" + str(initial_scene)
                )
            ]
        ),
        config=types.GenerateContentConfig(
            system_instruction=INITIAL_FRAME_GENERATION_PROMPT,
            temperature=0.9,
            top_k=2,
            top_p=1.0,
            thinking_config=types.ThinkingConfig(
                thinking_budget=-1
            )
        )
    )
    
    print("Generated prompt for Initial frame generation:\n", response.text)

    return response.text

def _generate_initial_frame():

    initial_frame_generation_prompt = _generate_prompt_for_initial_frame()

    frame_1 = types.Part.from_uri(
        file_uri="gs://in3-brand-guidelines/Brand guidelines /reference_images_for_video_generation/frame_1.jpg",
        mime_type="image/jpg"
    )

    frame_2 = types.Part.from_uri(
        file_uri="gs://in3-brand-guidelines/Brand guidelines /reference_images_for_video_generation/frame_314.jpg",
        mime_type="image/jpg"
    )

    visual_reference = types.Part.from_uri(
        file_uri="gs://in3-brand-guidelines/Brand guidelines /images/visual_template.png",
        mime_type="image/png"
    )

    # print(initial_frame_generation_prompt)
    input_text = types.Part.from_text(
        text=initial_frame_generation_prompt
    )

    contents = types.Content(
        role="user",
        parts=[frame_1, frame_2, visual_reference, input_text]
    )

    # Generate config
    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_k=1,
        image_config = types.ImageConfig(
            aspect_ratio="16:9"
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

    response = gemini_client.models.generate_content(
        model="gemini-2.5-flash-image",
        contents=contents,
        config=generate_content_config
    )

    # Extract image bytes from the response
    image_bytes = response.candidates[0].content.parts[0].inline_data.data

    first_frame = types.Part.from_bytes(
        data=image_bytes, mime_type="image/png"
    )

    # with open("initial_frame.png", "wb") as file:
    #     file.write(image_bytes)

    return first_frame

def _get_last_frame_from_uri(uri: str) -> types.Part:
    """
    Given a GCS URI of a video, download the video and extract the last frame as PNG bytes.

    Args:
        uri (str): Full GCS URI of the video, e.g., 'gs://video-results/4073235090597147577/sample_0.mp4'.

    Returns:
        types.Part: Last frame image wrapped in Part with mime_type "image/png".
    """
    if not uri.startswith("gs://"):
        raise ValueError("URI must start with 'gs://'")

    # Parse bucket and blob path
    parts = uri[5:].split("/", 1)
    bucket_name = parts[0]
    blob_path = parts[1]

    print(f"Fetching video: gs://{bucket_name}/{blob_path}")

    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_path)

    # Download video to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as temp_file:
        blob.download_to_filename(temp_file.name)
        video_path = temp_file.name

    try:
        # Extract last frame with OpenCV
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise RuntimeError("Could not open video for reading.")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
        ret, frame = cap.read()
        cap.release()

        if not ret:
            raise RuntimeError("Failed to read last frame from video.")

        # Encode to PNG bytes
        success, buffer = cv2.imencode(".png", frame)
        if not success:
            raise RuntimeError("Failed to encode last frame to PNG.")

        # Wrap as Part object
        last_frame_image = types.Part.from_bytes(data=buffer.tobytes(), mime_type="image/png")
        return last_frame_image

    finally:
        # Ensure temporary file is deleted
        os.remove(video_path)

def video_generation_func():
    """
    Use this tool to generate videos.

    Generate videos scene by scene using Gemini model, maintain continuity
    by using the last frame of the previous video, and stitch all scenes
    into a single final video.
    """

    final_video_storage_bucket_name = "marketing_agent_artifacts"
    final_video_storage_bucket = storage_client.bucket(
        bucket_name=final_video_storage_bucket_name
    )

    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "sub_agents", "script_writer_agent", "ad_script", "ad_video_script.json")

    with open(script_path, "r", encoding="utf-8") as f:
        video_script = json.load(f)  # use json.load, not json.loads
        
    scenes = video_script['scenes']
    generated_videos_uri = []

    # Generate the initial frame for the first scene
    initial_frame = _generate_initial_frame()

    for i, scene in enumerate(scenes):
        print(f"Generating video for scene {i+1}/{len(scenes)}: {scene['scene_title']}")

        # For subsequent scenes, get the last frame of the previous video
        if i > 0:
            previous_video_uri = generated_videos_uri[-1]
            initial_frame = _get_last_frame_from_uri(previous_video_uri)

        # Start the video generation operation
        operation = veo_client.models.generate_videos(
            model="veo-3.0-generate-001",
            source=types.GenerateVideosSource(
                prompt=str(scene),
                image=initial_frame.as_image(),
            ),
            config=types.GenerateVideosConfig(
                output_gcs_uri="gs://video-results",
            ),
        )

        # Poll until the operation is done
        op = types.GenerateVideosOperation(name=operation.name)
        while not op.done:
            print("Video generation in progress... waiting 10 seconds")
            time.sleep(10)
            op = veo_client.operations.get(op)

        # Now operation.response is available
        if op.response and op.response.generated_videos:
            generated_video_uri = op.response.generated_videos[0].video.uri
            generated_videos_uri.append(generated_video_uri)
            print(f"Scene {i+1} video generated: {generated_video_uri}")
        else:
            raise RuntimeError(f"Video generation failed for scene {i+1}")

    print("All scene videos generated. Proceeding to stitching...")

    # ---- Stitching logic ----
    temp_files = []
    clips = []

    for i, uri in enumerate(generated_videos_uri):
        # Parse bucket and blob path from URI
        if not uri.startswith("gs://"):
            raise ValueError(f"Invalid URI: {uri}")
        parts = uri[5:].split("/", 1)
        bucket_name = parts[0]
        blob_path = parts[1]

        # Download video to temp file
        bucket = storage_client.bucket(bucket_name)
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
        bucket.blob(blob_path).download_to_filename(temp_file.name)
        temp_files.append(temp_file.name)

        # Load video clip
        clip = VideoFileClip(temp_file.name)
        clips.append(clip)
        print(f"Downloaded video {i+1}: gs://{bucket_name}/{blob_path}")

    # Concatenate all clips with audio
    final_clip = concatenate_videoclips(clips, method="compose")

    # Save final stitched video to temp file
    stitched_temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    stitched_temp_file.close()
    final_clip.write_videofile(stitched_temp_file.name, codec="libx264", audio_codec="aac")

    # Read final video bytes
    with open(stitched_temp_file.name, "rb") as f:
        video_bytes = f.read()

    # Cleanup
    for clip in clips:
        clip.close()
    for f in temp_files:
        os.remove(f)
    os.remove(stitched_temp_file.name)

    print("Final stitched video with audio generated successfully.")

    # final_ad_video = types.Part.from_bytes(
    #     data=video_bytes, mime_type="video/mp4"
    # )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") 
    destination_blob = f"ad_campaign_video/{timestamp}_{uuid.uuid4().hex[:8]}.mp4"
    blob = final_video_storage_bucket.blob(destination_blob)
    blob.upload_from_string(
        data=video_bytes,
        content_type="video/mp4"
    )

    # with open("generated_video.mp4", "wb") as file:
    #     file.write(video_bytes)

    # return final_ad_video

    return {
        "Status": "Ad campaign video generated successfully",
        "Ad_Video_Campaign_Public_URL": f"https://storage.cloud.google.com/{final_video_storage_bucket_name}/{destination_blob}",
    }
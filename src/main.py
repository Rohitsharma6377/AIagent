import os
import sys
import asyncio

# Add the project root to the Python path to resolve module import issues
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
import random
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

from src.content_creation.creator import create_video_ffmpeg
from src.youtube.uploader import upload_to_youtube
from src.instagram.uploader import upload_reel

# --- Configuration ---
TARGET_PLATFORM = 'both'  # 'youtube', 'instagram', or 'both'

# Test topic (while trends fetching is being fixed)
TEST_TOPICS = [
    "Artificial Intelligence in 2024",
    "Latest Technology Trends",
    "Digital Innovation Today",
    "Future of Technology"
]

async def main():
    """
    Main function to run the video creation and uploading process.
    """
    load_dotenv()
    
    # Use a test topic instead of fetching trends
    video_topic = random.choice(TEST_TOPICS)
    print(f"\nSelected Topic for Video: '{video_topic}'")

    # --- Video Specifications (now using the test topic) ---
    youtube_title = f"AI-Generated Short on {video_topic}"
    youtube_description = f"A 1-minute AI-generated YouTube Short about {video_topic}."
    youtube_tags = ["AI", "Shorts", "Tech", video_topic]
    instagram_caption = f"Check out this reel on {video_topic}! #AI #Tech #Future #{video_topic.replace(' ', '')}"

    if TARGET_PLATFORM in ['youtube', 'both']:
        print("--- Starting YouTube Video Process ---")
        video_path = await create_video_ffmpeg(
            topic=video_topic,
            duration=60,  # 1 minute
            aspect_ratio='portrait'
        )
        if video_path:
            print(f"YouTube video created: {video_path}")
            upload_to_youtube(
                file_path=video_path,
                title=youtube_title,
                description=youtube_description,
                tags=youtube_tags
            )
        else:
            print("Failed to create video for YouTube. Skipping upload.")

    if TARGET_PLATFORM in ['instagram', 'both']:
        print("\n--- Starting Instagram Reel Process ---")
        reel_path = await create_video_ffmpeg(
            topic=video_topic,
            duration=30,  # 30 seconds
            aspect_ratio='portrait'
        )
        if reel_path:
            print(f"Instagram Reel created: {reel_path}")
            upload_reel(
                video_path=reel_path,
                caption=instagram_caption
            )
        else:
            print("Failed to create Reel for Instagram. Skipping upload.")

if __name__ == "__main__":
    asyncio.run(main())

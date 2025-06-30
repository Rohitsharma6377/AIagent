import os
import asyncio
from pathlib import Path
from instagrapi import Client
from dotenv import load_dotenv

async def upload_reel(video_path, caption, first_comment=""):
    """
    Upload a video as a Reel to Instagram using a pre-saved session file.
    
    Args:
        video_path (str): Path to the video file
        caption (str): Caption for the Reel
        first_comment (str): Optional first comment to post
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    cl = Client()
    
    session_file = Path("session.json")
    if not session_file.exists():
        print("\n--- INSTAGRAM LOGIN REQUIRED ---")
        print(f"Session file '{session_file}' not found.")
        print("Please run the login helper script once to authorize the application:")
        print("python src/instagram/login_helper.py")
        print("--------------------------------\n")
        return

    try:
        print("Logging in to Instagram using session file.")
        cl.load_settings(session_file)

        print("Uploading Reel to Instagram...")
        media = cl.clip_upload(
            video_path,
            caption=caption
        )
        print("Reel uploaded successfully!")
        
        if first_comment:
            cl.media_comment(media.id, first_comment)
            print("Posted first comment.")
            
    except Exception as e:
        print(f"An error occurred during Reel upload: {e}")

if __name__ == "__main__":
    # For direct testing
    async def test_upload():
        test_video = "test_reel.mp4"
        if os.path.exists(test_video):
            await upload_reel(
                video_path=test_video,
                caption="Test Reel upload! #test"
            )
        else:
            print(f"Please create a test video file named '{test_video}' to test the uploader.")
    
    asyncio.run(test_upload())

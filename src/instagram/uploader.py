import os
import asyncio
from pathlib import Path
from instagrapi import Client
from dotenv import load_dotenv

async def upload_reel(video_path, caption, first_comment=""):
    """
    Upload a video as a Reel to Instagram using instagrapi.
    
    Args:
        video_path (str): Path to the video file
        caption (str): Caption for the Reel
        first_comment (str): Optional first comment to post
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    load_dotenv()
    username = os.getenv('INSTAGRAM_USERNAME')
    password = os.getenv('INSTAGRAM_PASSWORD')

    if not username or not password:
        print("Error: Instagram credentials not found in .env file")
        return

    cl = Client()
    
    # It's recommended to log in using a session file to avoid repeated logins
    session_file = Path("session.json")
    if session_file.exists():
        cl.load_settings(session_file)
        print("Logged in to Instagram using session file.")
    else:
        print("Logging in to Instagram with username and password...")
        cl.login(username, password)
        cl.dump_settings(session_file)
        print("Logged in and saved session.")

    try:
        print("Uploading Reel to Instagram...")
        # instagrapi uses clip_upload for Reels
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
        from dotenv import load_dotenv
        load_dotenv()
        
        test_video = "test_reel.mp4"
        if os.path.exists(test_video):
            await upload_reel(
                video_path=test_video,
                caption="Test Reel upload! #test"
            )
        else:
            print(f"Please create a test video file named '{test_video}' to test the uploader.")
    
    asyncio.run(test_upload())

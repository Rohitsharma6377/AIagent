import os
import asyncio
from pathlib import Path
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
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
        
        if media and media.id:
            print(f"  - Media ID: {media.id}")
            if media.code:
                print(f"  - Reel URL: https://www.instagram.com/reel/{media.code}/")

        if first_comment:
            cl.media_comment(media.id, first_comment)
            print("Posted first comment.")

    except LoginRequired:
        print("\n--- INSTAGRAM LOGIN EXPIRED ---")
        print("Your session has expired or is invalid.")
        print("Please run the login helper script again to re-authorize:")
        print("python src/instagram/login_helper.py")
        print("---------------------------------\n")
    except Exception as e:
        error_str = str(e)
        if 'feedback_required' in error_str:
            print("\n[INSTAGRAM BLOCK] 'feedback_required' error detected. Instagram is restricting uploads due to suspected automation or policy violation.")
            print("Uploads will be paused. Please check your Instagram app for any required verification or wait several hours before resuming.")
            # Create a flag file to signal main loop to pause
            with open('feedback_required.flag', 'w') as f:
                f.write('Instagram feedback_required triggered. Manual action may be needed.')
            # Raise a custom exception to be caught by the main loop
            raise RuntimeError('INSTAGRAM_FEEDBACK_REQUIRED')
        print(f"An unknown error occurred during Reel upload: {e}")

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

import os
from instagrapi import Client
from instagrapi.types import Usertag

def upload_reel(video_path, caption, first_comment=""):
    """
    Uploads a video to Instagram as a Reel.

    Args:
        video_path (str): The path to the video file.
        caption (str): The caption for the Reel.
        first_comment (str): An optional first comment to post.
    """
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    username = os.getenv("INSTAGRAM_USERNAME")
    password = os.getenv("INSTAGRAM_PASSWORD")
    
    if not username or not password:
        print("Error: INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD must be set in your .env file.")
        return

    cl = Client()
    
    # It's recommended to log in using a session file to avoid repeated logins
    session_file = "session.json"
    if os.path.exists(session_file):
        cl.load_settings(session_file)
        print("Logged in using session file.")
    else:
        print("Logging in with username and password...")
        cl.login(username, password)
        cl.dump_settings(session_file)
        print("Logged in and saved session.")

    try:
        print("Uploading Reel...")
        # Instagram Reels are uploaded via the clip_upload method
        media = cl.clip_upload(
            video_path,
            caption=caption,
            # You can add usertags or location here if desired
            # usertags=[Usertag(user=cl.user_info_by_username("instagram"), x=0.5, y=0.5)],
            # location=cl.location_search("Paris, France")[0]
        )
        print("Reel uploaded successfully!")

        if first_comment:
            cl.media_comment(media.id, first_comment)
            print("Posted first comment.")

    except Exception as e:
        print(f"An error occurred during Reel upload: {e}")

if __name__ == '__main__':
    # For direct testing
    from dotenv import load_dotenv
    load_dotenv()
    if not (os.getenv("INSTAGRAM_USERNAME") and os.getenv("INSTAGRAM_PASSWORD")):
        print("Please set INSTAGRAM_USERNAME and INSTAGRAM_PASSWORD in your .env file to test.")
    else:
        # You would need a video file named 'test_reel.mp4' in the root directory.
        # if os.path.exists('test_reel.mp4'):
        #    upload_reel('test_reel.mp4', 'This is a test Reel from my AI Agent!')
        # else:
        print("This script is meant to be imported, not run directly.")
        print("To test, create a short portrait video named 'test_reel.mp4' in the root.")

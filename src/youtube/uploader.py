import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

"""
IMPORTANT: Before running this script, you need to:
1. Go to Google Cloud Console (https://console.cloud.google.com)
2. Select your project
3. Go to APIs & Services > Credentials
4. Edit your OAuth 2.0 Client ID
5. Add this to "Authorized redirect URIs": http://localhost:8080/
6. Download the updated client_secrets.json
"""

# OAuth 2.0 credentials
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']
TOKEN_PICKLE_FILE = 'token.pickle'
OAUTH_PORT = 8080

def get_authenticated_service():
    """Get YouTube API credentials and build service."""
    credentials = None
    
    # Token pickle stores the user's credentials from previously successful logins
    if os.path.exists(TOKEN_PICKLE_FILE):
        print('Loading credentials from file...')
        with open(TOKEN_PICKLE_FILE, 'rb') as token:
            credentials = pickle.load(token)

    # If there are no valid credentials available, prompt the user to log in
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            print('Refreshing access token...')
            credentials.refresh(Request())
        else:
            print('Fetching new tokens...')
            try:
                flow = InstalledAppFlow.from_client_secrets_file(
                    'client_secrets.json', SCOPES)
                credentials = flow.run_local_server(port=OAUTH_PORT)
            except Exception as e:
                print(f"\nError during OAuth: {e}")
                print("\nPlease make sure:")
                print(f"1. Your client_secrets.json has http://localhost:{OAUTH_PORT}/ in its redirect_uris")
                print("2. The same URI is added in Google Cloud Console")
                print("3. You've enabled the YouTube Data API v3")
                raise

        # Save the credentials for the next run
        with open(TOKEN_PICKLE_FILE, 'wb') as token:
            print('Saving credentials for future use...')
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def upload_to_youtube(file_path, title, description="", tags=None):
    """
    Upload a video to YouTube.
    
    Args:
        file_path (str): Path to the video file
        title (str): Title of the video
        description (str): Video description
        tags (list): List of tags for the video
    """
    if not os.path.exists(file_path):
        print(f"Error: Video file not found at {file_path}")
        return

    print("Authenticating with YouTube...")
    try:
        youtube = get_authenticated_service()
        
        print("Preparing video upload...")
        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': tags or [],
                'categoryId': '22'  # People & Blogs category
            },
            'status': {
                'privacyStatus': 'private',  # Start as private for safety
                'selfDeclaredMadeForKids': False
            }
        }

        # Create the video insert request
        insert_request = youtube.videos().insert(
            part=','.join(body.keys()),
            body=body,
            media_body=MediaFileUpload(
                file_path, 
                chunksize=-1, 
                resumable=True
            )
        )

        print("Starting video upload to YouTube...")
        response = insert_request.execute()
        
        video_id = response.get('id')
        if video_id:
            print(f"Video upload successful! Video ID: {video_id}")
            print(f"Video URL: https://youtu.be/{video_id}")
        else:
            print("Video upload completed but no video ID was returned.")

    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
    except Exception as e:
        print(f"An error occurred during upload: {e}")

if __name__ == "__main__":
    # For direct testing
    from dotenv import load_dotenv
    load_dotenv()
    
    test_video = "test_video.mp4"
    if os.path.exists(test_video):
        upload_to_youtube(
            file_path=test_video,
            title="Test Upload",
            description="This is a test upload",
            tags=["test", "upload"]
        )
    else:
        print(f"Please create a test video file named '{test_video}' to test the uploader.")

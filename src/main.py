import os
import sys
import time
import asyncio
import random
import re
from datetime import datetime
from dotenv import load_dotenv

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trending.google_trends import TrendingTopicsFetcher
from src.content_creation.creator import create_video
from src.youtube.uploader import upload_to_youtube
from src.instagram.uploader import upload_reel

def sanitize_hashtag(text):
    """Removes special characters to create a valid hashtag."""
    return re.sub(r'[^a-zA-Z0-9]', '', text)

async def create_and_upload_youtube_video(topic, output_dir):
    """Creates and uploads a 3-minute YouTube video."""
    try:
        print(f"\n--- Creating 3-Minute YouTube Video for: {topic} ---")
        video_path = await create_video(
            topic=topic,
            duration=180,  # 3 minutes
            aspect_ratio='landscape',
            output_dir=output_dir
        )
        
        if video_path and os.path.exists(video_path):
            print(f"\n--- Uploading to YouTube: {topic} ---")
            title = f"{topic} (Full Video in Hindi)"
            description = f"A detailed 3-minute video exploring {topic}. All content is AI-generated."
            tags = ['AI', 'DeepDive', 'Hindi', 'Tech', topic]
            
            try:
                # Run the synchronous upload function in a separate thread with a timeout
                await asyncio.wait_for(
                    asyncio.to_thread(upload_to_youtube, video_path, title, description, tags),
                    timeout=60.0
                )
            except asyncio.TimeoutError:
                print("\nYouTube upload timed out after 60 seconds. Continuing to the next task.")
        
    except Exception as e:
        print(f"An error occurred during YouTube video processing for '{topic}': {e}")
        print("This may be due to an API quota issue. Continuing to the next task.")

async def create_and_upload_instagram_reel(topic, output_dir):
    """Creates and uploads a 1-minute Instagram Reel."""
    try:
        print(f"\n--- Creating 1-Minute Instagram Reel for: {topic} ---")
        if not topic or not topic.strip():
            print("WARNING: Topic is empty or None. Skipping Instagram upload.")
            return
        reel_path = await create_video(
            topic=topic,
            duration=60,  # 1 minute
            aspect_ratio='portrait',
            output_dir=output_dir
        )
        
        if reel_path and os.path.exists(reel_path):
            print(f"\n--- Uploading to Instagram: {topic} ---")
            safe_hashtag = sanitize_hashtag(topic)
            category_hashtag = f"#{sanitize_hashtag(os.getenv('CURRENT_CATEGORY', ''))}"
            
            # Create a more dynamic set of hashtags
            base_hashtags = "#HindiReels #AI #Trending"
            topic_hashtag = f"#{safe_hashtag}"
            caption = f"🎥 {topic}\n\n{base_hashtags} {topic_hashtag} {category_hashtag}"
            print(f"[DEBUG] Instagram caption to be used:\n{caption}\n")
            await upload_reel(reel_path, caption)
            print(f"--- Finished Instagram task for: {topic} ---")

    except Exception as e:
        print(f"An error occurred during Instagram Reel processing for '{topic}': {e}")
        print("This may be due to an API quota issue. Continuing to the next task.")


async def main_cycle(output_dir):
    """Runs one complete cycle of fetching a topic and creating videos."""
    trends_fetcher = TrendingTopicsFetcher(region='IN')
    
    # 1. Select a category
    categories = trends_fetcher.get_available_categories()
    if not categories:
        print("No categories found. Waiting for the next cycle.")
        return
    category = random.choice(categories)
    os.environ['CURRENT_CATEGORY'] = category # Save for later use in caption
    
    # 2. Get a topic from that category
    print(f"\n>>> Selected Category for this cycle: {category} <<<")
    topics = trends_fetcher.get_topics(category)
    
    if not topics:
        print(f"Could not fetch any topics for '{category}'. Waiting for the next cycle.")
        return
        
    topic = random.choice(topics)
    print(f">>> Selected Topic for this cycle: {topic} <<<")

    # Read configuration from .env file
    create_youtube = os.getenv('CREATE_YOUTUBE_VIDEO', 'True').lower() in ('true', '1', 't')
    create_instagram = os.getenv('CREATE_INSTAGRAM_REEL', 'True').lower() in ('true', '1', 't')

    if create_youtube:
        await create_and_upload_youtube_video(topic, output_dir)
    else:
        print("\nSkipping YouTube video creation based on .env configuration.")

    if create_instagram:
        await create_and_upload_instagram_reel(topic, output_dir)
    else:
        print("\nSkipping Instagram Reel creation based on .env configuration.")


if __name__ == "__main__":
    load_dotenv()
    
    if not os.path.exists('client_secrets.json'):
        print("FATAL: client_secrets.json not found. Please obtain it from Google Cloud Console.")
    else:
        while True:
            output_dir = os.path.join("output", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.makedirs(output_dir, exist_ok=True)
            
            asyncio.run(main_cycle(output_dir))
            
            print("\n\n>>> Cycle complete. Waiting for 1 minute before starting the next one... <<<")
            time.sleep(60)

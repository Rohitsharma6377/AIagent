import os
import sys
import time
import asyncio
import random
import re
import pickle
from datetime import datetime
from dotenv import load_dotenv
import requests
from pathlib import Path

# Add project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.trending.google_trends import TrendingTopicsFetcher, FALLBACK_TOPICS
from src.content_creation.creator import create_video, random_upload_delay
from src.youtube.uploader import upload_to_youtube
from src.instagram.uploader import upload_reel

# Persistent storage for used voice reel topics and reel count
USED_VOICE_REEL_TOPICS_FILE = 'used_voice_reel_topics.pkl'
REEL_COUNT_FILE = 'reel_count.pkl'

def load_pickle(filename, default):
    if os.path.exists(filename):
        with open(filename, 'rb') as f:
            return pickle.load(f)
    return default

def save_pickle(filename, obj):
    with open(filename, 'wb') as f:
        pickle.dump(obj, f)

# Load persistent state
used_voice_reel_topics = load_pickle(USED_VOICE_REEL_TOPICS_FILE, set())
reel_count = load_pickle(REEL_COUNT_FILE, 0)

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

def fetch_song_metadata(song_url):
    # Dummy: Extracts song title/artist from URL or returns placeholders
    # In production, parse ID3 tags or use API if available
    if 'jamendo' in song_url:
        # Jamendo URLs have /track/ID/SONGNAME.mp3
        parts = song_url.split('/')
        if len(parts) > 5:
            title = parts[-1].replace('.mp3', '').replace('-', ' ').title()
            artist = 'Jamendo Artist'
            return title, artist
    # Fallback for samplelib or others
    return 'Trending Song', 'Unknown Artist'

def generate_caption(topic, category, song_title=None, song_artist=None, is_music_reel=False):
    if is_music_reel and song_title:
        # Try to fetch a related quote/lyric (placeholder logic)
        quote = f"Enjoy the vibes of '{song_title}' by {song_artist}. Let the music move you!"
        caption = f"{quote} #NowPlaying"
        if len(caption) > 150:
            caption = caption[:147] + '...'
        return caption
    # Voice/topic-based
    base = f"{topic}: Discover more in {category}. "
    words = (base * 5).split()[:random.randint(40, 60)]
    caption = ' '.join(words)
    if len(caption) > 150:
        caption = caption[:147] + '...'
    return caption

def generate_hashtags(topic, category, n=30, song_title=None, song_artist=None, is_music_reel=False):
    tags = set()
    if is_music_reel and song_title:
        tags.add(f"#{sanitize_hashtag(song_title)}")
        tags.add(f"#{sanitize_hashtag(song_artist)}")
        tags.add("#NowPlaying")
        tags.add("#MusicReel")
        tags.add("#TrendingSong")
    tags.add(f"#{sanitize_hashtag(topic)}")
    tags.add(f"#{sanitize_hashtag(category)}")
    generic_tags = [
        'Trending', 'Viral', 'Explore', 'Reels', 'Music', 'Fun', 'InstaGood', 'AI', '2024',
        'Hindi', 'Punjabi', 'English', 'India', 'Desi', 'Bollywood', 'Pop', 'Rap', 'Dance',
        'Motivation', 'Learning', 'Vibes', 'Chill', 'Love', 'Life', 'Friends', 'Family',
        'Comedy', 'Memes', 'Tech', 'Science', 'Business', 'Sports', 'Health', 'Travel',
        'Culture', 'Art', 'Fashion', 'Food', 'Fitness', 'Education', 'Inspiration', 'Quotes',
        'Photography', 'Nature', 'Adventure', 'Goals', 'Dreams', 'Success', 'Happiness',
        'PositiveVibes', 'Mindset', 'SelfCare', 'Creativity', 'Story', 'Shorts', 'Vlog',
        'Vlogger', 'Vlogging', 'ViralVideo', 'ViralReel', 'ForYou', 'ForYouPage', 'FYP',
        'ExplorePage', 'Discover', 'MusicLover', 'Song', 'Singer', 'Artist', 'Beat', 'Sound',
        'Lyrics', 'Cover', 'Remix', 'Mashup', 'Original', 'New', 'Now', 'Today', 'ThisWeek',
        'ThisMonth', 'TrendingNow', 'MustWatch', 'WatchThis', 'Share', 'Like', 'Comment',
        'Follow', 'Subscribe', 'Support', 'Community', 'Collab', 'Creator', 'Influencer',
        'ViralContent', 'ContentCreator', 'SocialMedia', 'Online', 'Digital', 'TechTrends',
        'Future', 'Innovation', 'Startup', 'Entrepreneur', 'Motivational', 'Learning',
        'Education', 'Knowledge', 'Wisdom', 'Growth', 'PersonalGrowth', 'SelfImprovement',
        'Challenge', 'FunChallenge', 'Game', 'Games', 'Gaming', 'Gamer', 'Play', 'Win',
        'Champion', 'Leader', 'Team', 'Squad', 'SquadGoals', 'Best', 'Top', 'Amazing',
        'Awesome', 'Cool', 'Wow', 'OMG', 'Incredible', 'Unbelievable', 'MustSee', 'Epic',
        'Legend', 'Legendary', 'Iconic', 'Classic', 'Throwback', 'Memories', 'OldIsGold',
        'Timeless', 'Forever', 'Always', 'NeverGiveUp', 'KeepGoing', 'StayStrong', 'Believe',
        'DreamBig', 'WorkHard', 'SuccessStory', 'Journey', 'Path', 'Road', 'Way', 'Direction',
        'Move', 'Action', 'Act', 'DoIt', 'JustDoIt', 'LetsGo', 'GoForIt', 'MakeItHappen',
        'Yes', 'No', 'Maybe', 'WhyNot', 'Try', 'TryAgain', 'NeverStop', 'KeepMoving', 'Push',
        'Rise', 'Shine', 'Glow', 'Spark', 'Fire', 'Energy', 'Power', 'Strength', 'Force',
        'Magic', 'Wonder', 'Surprise', 'Gift', 'Present', 'Moment', 'Time', 'Day', 'Night',
        'Morning', 'Evening', 'Afternoon', 'Sun', 'Moon', 'Star', 'Sky', 'Cloud', 'Rain',
        'Storm', 'Wind', 'Earth', 'Water', 'Fire', 'Air', 'Space', 'Universe', 'Galaxy',
        'Planet', 'World', 'Life', 'Live', 'Living', 'Exist', 'Being', 'Human', 'People',
        'Person', 'Individual', 'Unique', 'Special', 'Different', 'Diversity', 'Unity', 'Together',
        'One', 'All', 'Everyone', 'Somebody', 'Nobody', 'Somewhere', 'Anywhere', 'Everywhere',
        'Nowhere', 'Here', 'There', 'Where', 'When', 'How', 'What', 'Why', 'Which', 'Who',
        'Whom', 'Whose', 'Whichever', 'Whatever', 'Whenever', 'However', 'Because', 'Since',
        'Until', 'While', 'During', 'Before', 'After', 'Once', 'Twice', 'Thrice', 'Again',
        'Soon', 'Later', 'Early', 'Late', 'First', 'Last', 'Next', 'Previous', 'Past', 'Future',
        'Present', 'Current', 'Recent', 'Old', 'New', 'Young', 'Youth', 'Adult', 'Child', 'Kid',
        'Baby', 'Teen', 'Elder', 'Senior', 'Parent', 'Mother', 'Father', 'Sister', 'Brother',
        'Daughter', 'Son', 'Wife', 'Husband', 'Friend', 'Buddy', 'Pal', 'Mate', 'Partner',
        'Colleague', 'Boss', 'Leader', 'Manager', 'Worker', 'Employee', 'Employer', 'Owner',
        'Customer', 'Client', 'User', 'Member', 'Guest', 'Visitor', 'Host', 'Admin', 'Moderator',
        'Supporter', 'Fan', 'Follower', 'Subscriber', 'Viewer', 'Audience', 'Spectator', 'Observer',
        'Participant', 'Contestant', 'Competitor', 'Winner', 'Loser', 'Player', 'Coach', 'Trainer',
        'Mentor', 'Guide', 'Advisor', 'Consultant', 'Expert', 'Specialist', 'Professional', 'Amateur',
        'Beginner', 'Novice', 'Learner', 'Student', 'Teacher', 'Professor', 'Instructor', 'Educator',
        'Researcher', 'Scientist', 'Engineer', 'Doctor', 'Nurse', 'Therapist', 'Counselor', 'Psychologist',
        'Artist', 'Musician', 'Singer', 'Dancer', 'Actor', 'Actress', 'Director', 'Producer', 'Writer',
        'Author', 'Poet', 'Journalist', 'Reporter', 'Editor', 'Publisher', 'Photographer', 'Designer',
        'Developer', 'Programmer', 'Coder', 'Hacker', 'Maker', 'Builder', 'Creator', 'Inventor',
        'Entrepreneur', 'Businessman', 'Businesswoman', 'Investor', 'Trader', 'Broker', 'Agent', 'Dealer',
        'Merchant', 'Shopkeeper', 'Vendor', 'Supplier', 'Manufacturer', 'Distributor', 'Wholesaler',
        'Retailer', 'Customer', 'Client', 'User', 'Member', 'Guest', 'Visitor', 'Host', 'Admin',
        'Moderator', 'Supporter', 'Fan', 'Follower', 'Subscriber', 'Viewer', 'Audience', 'Spectator',
        'Observer', 'Participant', 'Contestant', 'Competitor', 'Winner', 'Loser', 'Player', 'Coach',
        'Trainer', 'Mentor', 'Guide', 'Advisor', 'Consultant', 'Expert', 'Specialist', 'Professional',
        'Amateur', 'Beginner', 'Novice', 'Learner', 'Student', 'Teacher', 'Professor', 'Instructor',
        'Educator', 'Researcher', 'Scientist', 'Engineer', 'Doctor', 'Nurse', 'Therapist', 'Counselor',
        'Psychologist', 'Artist', 'Musician', 'Singer', 'Dancer', 'Actor', 'Actress', 'Director',
        'Producer', 'Writer', 'Author', 'Poet', 'Journalist', 'Reporter', 'Editor', 'Publisher',
        'Photographer', 'Designer', 'Developer', 'Programmer', 'Coder', 'Hacker', 'Maker', 'Builder',
        'Creator', 'Inventor', 'Entrepreneur', 'Businessman', 'Businesswoman', 'Investor', 'Trader',
        'Broker', 'Agent', 'Dealer', 'Merchant', 'Shopkeeper', 'Vendor', 'Supplier', 'Manufacturer',
        'Distributor', 'Wholesaler', 'Retailer'
    ]
    while len(tags) < n:
        tags.add(f"#{random.choice(generic_tags)}")
    return ' '.join(list(tags)[:n])

# Placeholder for Instagram trending audio selection
def get_trending_instagram_audio():
    # In production, replace with real API or scraping logic
    trending_audios = [
        'https://samplelib.com/lib/preview/mp3/sample-3s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-6s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-9s.mp3',
    ]
    return random.choice(trending_audios)

async def create_and_upload_instagram_reel(topic, output_dir, reel_index, voice_reel=False, use_spotify=True):
    try:
        print(f"\n--- Creating 1-Minute Instagram Reel for: {topic} ---")
        if not topic or not topic.strip():
            print("WARNING: Topic is empty or None. Skipping Instagram upload.")
            return
        # Check for Instagram session file
        session_file = Path("session.json")
        if not session_file.exists():
            print("\n--- INSTAGRAM LOGIN REQUIRED ---")
            print(f"Session file '{session_file}' not found.")
            print("Please run the login helper script once to authorize the application:")
            print("python src/instagram/login_helper.py")
            print("--------------------------------\n")
            print("Skipping Instagram upload for this cycle.")
            return
        # Pass voice_reel flag and use_spotify to create_video
        reel_path, song_url = await create_video(
            topic=topic,
            duration=60,  # 1 minute
            aspect_ratio='portrait',
            output_dir=output_dir,
            reel_index=reel_index,
            voice_reel=voice_reel,
            use_spotify=use_spotify
        )
        song_title, song_artist = None, None
        if not voice_reel and reel_path:
            song_title, song_artist = fetch_song_metadata(song_url) if song_url else (None, None)
        if reel_path and os.path.exists(reel_path):
            print(f"\n--- Uploading to Instagram: {topic} ---")
            category = os.getenv('CURRENT_CATEGORY', '')
            caption = generate_caption(topic, category, song_title, song_artist, is_music_reel=not voice_reel)
            hashtags = generate_hashtags(topic, category, song_title=song_title, song_artist=song_artist, is_music_reel=not voice_reel)
            full_caption = f"{caption}\n\n{hashtags}"
            print(f"[DEBUG] Instagram caption to be used:\n{full_caption}\n")
            await upload_reel(reel_path, full_caption)
            print(f"--- Finished Instagram task for: {topic} ---")
    except Exception as e:
        print(f"An error occurred during Instagram Reel processing for '{topic}': {e}")
        print("This may be due to an API quota issue. Continuing to the next task.")

async def main_cycle(output_dir, use_spotify):
    global reel_count, used_voice_reel_topics
    trends_fetcher = TrendingTopicsFetcher(region='IN')
    categories = trends_fetcher.get_available_categories()
    if not categories:
        print("No categories found. Waiting for the next cycle.")
        return
    category = random.choice(categories)
    os.environ['CURRENT_CATEGORY'] = category
    topics = trends_fetcher.get_topics(category)
    if not topics:
        print(f"Could not fetch any topics for '{category}'. Waiting for the next cycle.")
        return
    topic = random.choice(topics)
    print(f">>> Selected Topic for this cycle: {topic} <<<")
    create_youtube = os.getenv('CREATE_YOUTUBE_VIDEO', 'True').lower() in ('true', '1', 't')
    create_instagram = os.getenv('CREATE_INSTAGRAM_REEL', 'True').lower() in ('true', '1', 't')
    fallback = False
    if topic in FALLBACK_TOPICS.get(category, []):
        fallback = True
    if create_youtube:
        await create_and_upload_youtube_video(topic, output_dir)
    else:
        print("\nSkipping YouTube video creation based on .env configuration.")
    if create_instagram:
        reel_count += 1
        save_pickle(REEL_COUNT_FILE, reel_count)
        # Only every 5th reel is a voice reel, but only if use_spotify is True
        if use_spotify and reel_count % 5 == 0:
            available_voice_topics = [t for t in topics if t not in used_voice_reel_topics]
            if not available_voice_topics:
                used_voice_reel_topics = set()
                available_voice_topics = topics
            voice_topic = random.choice(available_voice_topics)
            used_voice_reel_topics.add(voice_topic)
            save_pickle(USED_VOICE_REEL_TOPICS_FILE, used_voice_reel_topics)
            print(f"[VOICE REEL] Creating unique voice reel for topic: {voice_topic}")
            await create_and_upload_instagram_reel(voice_topic, output_dir, reel_count, voice_reel=True, use_spotify=use_spotify)
        else:
            await create_and_upload_instagram_reel(topic, output_dir, reel_count, voice_reel=False, use_spotify=use_spotify)
    else:
        print("\nSkipping Instagram Reel creation based on .env configuration.")

if __name__ == "__main__":
    load_dotenv()

    # Prompt user for audio source preference
    use_spotify = None
    while use_spotify is None:
        user_input = input("Do you want to use Spotify/online sources for music reels? (yes/no): ").strip().lower()
        if user_input in ("yes", "y"): use_spotify = True
        elif user_input in ("no", "n"): use_spotify = False
        else: print("Please enter 'yes' or 'no'.")

    if not os.path.exists('client_secrets.json'):
        print("FATAL: client_secrets.json not found. Please obtain it from Google Cloud Console.")
    else:
        while True:
            # Check for Instagram feedback_required flag
            if os.path.exists('feedback_required.flag'):
                print("\n[BLOCKED] Instagram 'feedback_required' flag detected. Pausing uploads for 6 hours. Please check your Instagram app for verification or wait before resuming.")
                time.sleep(6 * 60 * 60)  # Sleep for 6 hours
                continue
            output_dir = os.path.join("output", datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
            os.makedirs(output_dir, exist_ok=True)
            asyncio.run(main_cycle(output_dir, use_spotify=use_spotify))
            print("\n\n>>> Cycle complete. Waiting before starting the next one... <<<")
            random_upload_delay()

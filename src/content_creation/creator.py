import os
import shutil
import asyncio
import requests
import textwrap
import random
import time
import json
import re
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, TextClip, ImageClip
)
import moviepy.audio.fx.all as afx
from src.content_creation.script_generator import generate_script, parse_script_to_dialogues
from src.content_creation.voice_generator import generate_realistic_voice, generate_multi_voice
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import urllib.request
import hashlib
import glob
import subprocess

# Subtitle creation is temporarily removed to prevent ImageMagick errors.
# def create_subtitle_clips(script, video_duration, video_size):
#     ...

async def download_media(url, path):
    """Asynchronously downloads a file."""
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(path, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

# Persistent storage for used (topic, video_url, song_url) combinations
USED_COMBINATIONS_FILE = 'used_reel_combinations.json'

def load_used_combinations():
    if os.path.exists(USED_COMBINATIONS_FILE):
        with open(USED_COMBINATIONS_FILE, 'r') as f:
            return set(tuple(x) for x in json.load(f))
    return set()

def save_used_combinations(used_combinations):
    with open(USED_COMBINATIONS_FILE, 'w') as f:
        json.dump([list(x) for x in used_combinations], f)

# Video categories/queries for unique backgrounds
VIDEO_CATEGORIES = ['love', 'couple', 'nature', 'city', 'animals', 'sports', 'dance', 'food', 'travel', 'art', 'fashion', 'technology', 'festival', 'party', 'adventure', 'ocean', 'mountain', 'forest', 'desert', 'rain', 'sunset']

# Music URLs for each language
MUSIC_TRACKS = {
    'english': [
        'https://samplelib.com/lib/preview/mp3/sample-3s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-6s.mp3',
    ],
    'punjabi': [
        'https://samplelib.com/lib/preview/mp3/sample-9s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-12s.mp3',
    ],
    'hindi': [
        'https://samplelib.com/lib/preview/mp3/sample-15s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-18s.mp3',
    ],
    'haryanvi': [
        'https://samplelib.com/lib/preview/mp3/sample-21s.mp3',
        'https://samplelib.com/lib/preview/mp3/sample-24s.mp3',
    ],
}

# Trending song clips for each language (replace with real URLs if available)
TRENDING_SONG_CLIPS = {
    'english': [
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3',
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3',
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3',
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-4.mp3',
    ],
    'punjabi': [
        'https://filesamples.com/samples/audio/mp3/sample1.mp3',  # Demo sample, replace with real Bhangra if available
        'https://filesamples.com/samples/audio/mp3/sample3.mp3',
        'https://filesamples.com/samples/audio/mp3/sample6.mp3',
        'https://filesamples.com/samples/audio/mp3/sample7.mp3',
    ],
    'hindi': [
        'https://filesamples.com/samples/audio/mp3/sample2.mp3',  # Demo sample, replace with real Bollywood if available
        'https://filesamples.com/samples/audio/mp3/sample5.mp3',
        'https://filesamples.com/samples/audio/mp3/sample8.mp3',
        'https://filesamples.com/samples/audio/mp3/sample10.mp3',
    ],
    'haryanvi': [
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-5.mp3',  # Use English as fallback
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-6.mp3',
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-7.mp3',
        'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-8.mp3',
    ],
}

# Video search queries for each language/theme
VIDEO_QUERIES = {
    'english': ['english party', 'english dance', 'english city', 'english friends'],
    'punjabi': ['punjabi dance', 'punjabi wedding', 'punjabi festival', 'punjabi bhangra'],
    'hindi': ['hindi movie', 'hindi dance', 'hindi festival', 'hindi city'],
    'haryanvi': ['haryanvi village', 'haryanvi dance', 'haryanvi festival', 'haryanvi wedding'],
}

# Jamendo API credentials (register for your own client_id at https://developer.jamendo.com/v3.0)
JAMENDO_CLIENT_ID = os.getenv('JAMENDO_CLIENT_ID', 'demo_client_id')

# Map language to Jamendo tags/genres
JAMENDO_LANG_TAGS = {
    'english': 'english',
    'punjabi': 'punjabi',
    'hindi': 'hindi',
    'haryanvi': 'haryanvi',
}

def fetch_jamendo_song(language):
    """
    Fetch a trending song from Jamendo for the given language.
    Returns a direct MP3 URL or None if not found.
    """
    tag = JAMENDO_LANG_TAGS.get(language, 'english')
    url = f"https://api.jamendo.com/v3.0/tracks/?client_id={JAMENDO_CLIENT_ID}&format=json&limit=10&tags={tag}&audioformat=mp32&order=popularity_total"
    try:
        resp = requests.get(url)
        data = resp.json()
        tracks = data.get('results', [])
        for track in tracks:
            audio_url = track.get('audio')
            if audio_url:
                return audio_url
    except Exception as e:
        print(f"[Jamendo] Error fetching song for {language}: {e}")
    return None

# Helper to get the next unique (topic, video_url, song_url) for a non-voice reel
async def get_next_unique_combo(topic, used_combinations, lang, output_dir):
    api_key = os.getenv("PEXELS_API_KEY")
    for video_query in VIDEO_QUERIES[lang]:
        # Search Pexels for a video
        search_url = f"https://api.pexels.com/videos/search?query={video_query}&per_page=5&orientation=portrait"
        response = requests.get(search_url, headers={'Authorization': api_key})
        response.raise_for_status()
        videos_json = response.json().get('videos', [])
        for video_data in videos_json:
            video_url = next((f['link'] for f in video_data['video_files'] if f['quality'] == 'hd'), video_data['video_files'][0]['link'])
            for song_url in TRENDING_SONG_CLIPS[lang]:
                combo = (topic, video_url, song_url)
                if combo not in used_combinations:
                    # Download video to temp dir
                    video_path = os.path.join(output_dir, f"{lang}_{video_query.replace(' ','_')}_{video_data['id']}.mp4")
                    if not os.path.exists(video_path):
                        await download_media(video_url, video_path)
                    return combo, video_path, song_url
    # If all combinations used, reset
    used_combinations.clear()
    save_used_combinations(used_combinations)
    # Try again after reset
    return await get_next_unique_combo(topic, used_combinations, lang, output_dir)

def sanitize_filename(name):
    # Remove invalid characters for Windows paths
    return re.sub(r'[^a-zA-Z0-9_\- ]', '', name).replace(' ', '_')

# Persistent storage for used video URLs and (video, song) combos
USED_VIDEOS_FILE = 'used_videos_global.json'
USED_COMBOS_FILE = 'used_video_song_combos_global.json'

def load_used_videos():
    if os.path.exists(USED_VIDEOS_FILE):
        with open(USED_VIDEOS_FILE, 'r') as f:
            return set(json.load(f))
    return set()

def save_used_videos(used_videos):
    with open(USED_VIDEOS_FILE, 'w') as f:
        json.dump(list(used_videos), f)

def load_used_combos():
    if os.path.exists(USED_COMBOS_FILE):
        with open(USED_COMBOS_FILE, 'r') as f:
            return set(tuple(x) for x in json.load(f))
    return set()

def save_used_combos(used_combos):
    with open(USED_COMBOS_FILE, 'w') as f:
        json.dump([list(x) for x in used_combos], f)

# Spotify API helper
sp = None
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
print(f"[DEBUG] SPOTIFY_CLIENT_ID={'SET' if SPOTIFY_CLIENT_ID else 'NOT SET'}, SPOTIFY_CLIENT_SECRET={'SET' if SPOTIFY_CLIENT_SECRET else 'NOT SET'}")
if not SPOTIFY_CLIENT_ID or not SPOTIFY_CLIENT_SECRET:
    print("[ERROR] Spotify credentials are missing from your .env file. Please set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET.")
    raise RuntimeError("Spotify credentials missing. Cannot fetch Spotify previews.")
if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID,
        client_secret=SPOTIFY_CLIENT_SECRET
    ))

SPOTIFY_MARKET = {
    'english': 'US',
    'hindi': 'IN',
    'punjabi': 'IN',
}
SPOTIFY_PLAYLISTS = {
    'english': '37i9dQZEVXbLRQDuF5jeBp',  # US Top 50
    'hindi': '37i9dQZF1DXd8cOUiye1o2',    # Bollywood Top 50
    'punjabi': '37i9dQZF1DX5cZuAHLNjGz',  # Punjabi 101
}

SPOTIFY_ARTISTS = [
    'Justin Bieber',
    'Sidhu Moose Wala',
    'Arijit Singh',
    'Diljit Dosanjh',
    'Taylor Swift',
    'AP Dhillon',
]

def fetch_spotify_artist_top_preview():
    if not sp:
        return None, None, None
    random.shuffle(SPOTIFY_ARTISTS)
    for artist_name in SPOTIFY_ARTISTS:
        try:
            results = sp.search(q=f'artist:{artist_name}', type='artist', limit=1)
            items = results['artists']['items']
            if not items:
                continue
            artist_id = items[0]['id']
            top_tracks = sp.artist_top_tracks(artist_id)
            tracks = top_tracks['tracks']
            random.shuffle(tracks)
            for track in tracks:
                name = track['name']
                artist = track['artists'][0]['name']
                preview_url = track['preview_url']
                if preview_url:
                    print(f"[Spotify] Selected: {name} by {artist} - {preview_url}")
                    return name, artist, preview_url
        except Exception as e:
            print(f"[Spotify] Error fetching top tracks for {artist_name}: {e}")
    return None, None, None

async def create_video(topic: str, duration: int, aspect_ratio: str, output_dir: str = ".", music_url: str = None, reel_index: int = 0, voice_reel: bool = False, use_spotify: bool = True):
    """
    For non-voice reels: Use a trending song clip and a unique video (never repeat combination).
    For every 5th reel (voice_reel=True): Use the current voiceover logic and a unique video on the topic.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY environment variable not set.")
    # Sanitize topic for temp_dir
    safe_topic = sanitize_filename(topic)
    temp_dir = os.path.join(output_dir, f"temp_{safe_topic}_{random.randint(1000, 9999)}")
    os.makedirs(temp_dir, exist_ok=True)
    
    video_clips_handles = []
    created_successfully = False
    
    # Load used combinations
    used_videos = load_used_videos()
    used_combos = load_used_combos()
    
    try:
        if voice_reel:
            # --- Voice Reel: Generate script and voiceover, use unique video on topic ---
            print(f"\n1. Generating {int(duration/60)} min script for '{topic}' (voice reel)...")
            audio_path = os.path.join(temp_dir, "voiceover.mp3")
            script = generate_script(topic, duration)
            generate_realistic_voice(script, audio_path)
            for _ in range(10):
                if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                    break
                time.sleep(0.5)
            else:
                raise FileNotFoundError(f"Audio file was not created or is empty: {audio_path}")
            with AudioFileClip(audio_path) as voiceover_clip:
                actual_duration = voiceover_clip.duration
            # Search Pexels for a unique video on the topic
            search_url = f"https://api.pexels.com/videos/search?query={topic}&per_page=5&orientation=portrait"
            response = requests.get(search_url, headers={'Authorization': api_key})
            response.raise_for_status()
            videos_json = response.json().get('videos', [])
            for video_data in videos_json:
                video_url = next((f['link'] for f in video_data['video_files'] if f['quality'] == 'hd'), video_data['video_files'][0]['link'])
                combo = (topic, video_url, 'voice')
                if combo not in used_combos:
                    video_path = os.path.join(temp_dir, f"voice_{topic.replace(' ','_')}_{video_data['id']}.mp4")
                    await download_media(video_url, video_path)
                    used_combos.add(combo)
                    save_used_combos(used_combos)
                    break
            else:
                # If all combinations used, reset
                used_combos.clear()
                save_used_combos(used_combos)
                return await create_video(topic, duration, aspect_ratio, output_dir, music_url, reel_index, voice_reel, use_spotify)
            video_paths = [video_path]
            print(f"2. Assembling voice reel with unique video...")
            video_clips_handles = [VideoFileClip(vp) for vp in video_paths if os.path.exists(vp)]
            with concatenate_videoclips(video_clips_handles, method="compose") as background_video, \
                 AudioFileClip(audio_path) as main_audio_clip:
                looped_audio = afx.audio_loop(main_audio_clip, duration=background_video.duration)
                background_video.audio = looped_audio
                if main_audio_clip.duration < background_video.duration:
                    background_video = background_video.subclip(0, main_audio_clip.duration)
                final_clip = background_video
                final_video_path = os.path.join(output_dir, f"{safe_topic}_{aspect_ratio}_voice.mp4")
                final_clip.write_videofile(
                    final_video_path,
                    codec='libx264',
                    audio_codec='aac',
                    temp_audiofile=os.path.join(temp_dir, 'temp-audio.m4a'),
                    remove_temp=True,
                    threads=2,
                    preset='ultrafast',
                    logger='bar',
                    fps=24,
                    audio_fps=22050
                )
            print(f"Voice reel created successfully: {final_video_path}")
            created_successfully = True
            return final_video_path, None
        else:
            # For music reels, always use 30 seconds (Spotify preview duration)
            duration = 30
            langs = ['english', 'punjabi', 'hindi']
            lang = langs[reel_index % len(langs)]
            if not use_spotify:
                # Always use a local fallback MP3 from downloaded_songs/
                fallback_mp3s = glob.glob('downloaded_songs/*.mp3')
                if not fallback_mp3s:
                    print("[FALLBACK ERROR] No fallback MP3s found in downloaded_songs/. Skipping this music reel.")
                    return None, None
                fallback_song = random.choice(fallback_mp3s)
                print(f"[FALLBACK] Using local fallback song: {fallback_song}")
                # Use ffmpeg to extract a 30s clip starting at 20s
                audio_path = os.path.join(temp_dir, "song.mp3")
                try:
                    subprocess.run([
                        'ffmpeg', '-y', '-ss', '20', '-t', '30', '-i', fallback_song, '-acodec', 'libmp3lame', audio_path
                    ], check=True)
                except Exception as e:
                    print(f"[FALLBACK ERROR] Failed to extract middle clip: {e}")
                    return None, None
                song_url = fallback_song
                song_title = os.path.splitext(os.path.basename(fallback_song))[0]
                song_artist = "Fallback"
            else:
                # --- Use Spotify API for top artist track ---
                song_title, song_artist, preview_url = fetch_spotify_artist_top_preview()
                if not song_title or not song_artist or not preview_url:
                    print("[ERROR] Could not fetch a Spotify preview. Using fallback local song.")
                    # Fallback: use a random local MP3 from downloaded_songs/
                    fallback_mp3s = glob.glob('downloaded_songs/*.mp3')
                    if not fallback_mp3s:
                        print("[FALLBACK ERROR] No fallback MP3s found in downloaded_songs/. Skipping this music reel.")
                        return None, None
                    fallback_song = random.choice(fallback_mp3s)
                    print(f"[FALLBACK] Using local fallback song: {fallback_song}")
                    # Use ffmpeg to extract a 30s clip starting at 20s
                    audio_path = os.path.join(temp_dir, "song.mp3")
                    try:
                        subprocess.run([
                            'ffmpeg', '-y', '-ss', '20', '-t', '30', '-i', fallback_song, '-acodec', 'libmp3lame', audio_path
                        ], check=True)
                    except Exception as e:
                        print(f"[FALLBACK ERROR] Failed to extract middle clip: {e}")
                        return None, None
                    song_url = fallback_song
                    song_title = os.path.splitext(os.path.basename(fallback_song))[0]
                    song_artist = "Fallback"
                else:
                    audio_path = os.path.join(temp_dir, "song.mp3")
                    song_url = preview_url
                    print(f"[Spotify] Downloading preview audio: {song_url}")
                    try:
                        resp = requests.get(song_url, stream=True)
                        resp.raise_for_status()
                        with open(audio_path, 'wb') as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)
                        size = os.path.getsize(audio_path)
                        print(f"[Spotify] Preview audio downloaded: {audio_path} ({size} bytes)")
                        if size < 1000:
                            print(f"[Spotify] Downloaded file too small, not using: {audio_path}")
                            raise Exception("Downloaded preview is too small.")
                        # Save a copy in downloaded_songs
                        os.makedirs('downloaded_songs', exist_ok=True)
                        song_filename = f"{song_title or 'song'}_{song_artist or 'artist'}.mp3".replace(' ', '_')
                        song_save_path = os.path.join('downloaded_songs', song_filename)
                        shutil.copy(audio_path, song_save_path)
                    except Exception as e:
                        print(f"[ERROR] Failed to download Spotify preview audio: {e}. Skipping this music reel.")
                        return None, None
            # Search Pexels for a matching video, ensuring global uniqueness
            video_query = VIDEO_QUERIES[lang][reel_index % len(VIDEO_QUERIES[lang])]
            search_url = f"https://api.pexels.com/videos/search?query={video_query}&per_page=15&orientation=portrait"
            response = requests.get(search_url, headers={'Authorization': api_key})
            response.raise_for_status()
            videos_json = response.json().get('videos', [])
            video_path = None
            for video_data in videos_json:
                video_url = next((f['link'] for f in video_data['video_files'] if f['quality'] == 'hd'), video_data['video_files'][0]['link'])
                combo = (video_url, song_url)
                if video_url not in used_videos and combo not in used_combos:
                    video_path = os.path.join(temp_dir, f"{lang}_{video_query.replace(' ','_')}_{video_data['id']}.mp4")
                    await download_media(video_url, video_path)
                    used_videos.add(video_url)
                    used_combos.add(combo)
                    save_used_videos(used_videos)
                    save_used_combos(used_combos)
                    print(f"[INFO] Using unique video: {video_url}")
                    break
            if not video_path:
                # If all videos/combos used, reset and try again
                print("[RESET] All unique (video, song) pairs exhausted. Resetting global tracking.")
                used_videos.clear()
                used_combos.clear()
                save_used_videos(used_videos)
                save_used_combos(used_combos)
                return await create_video(topic, duration, aspect_ratio, output_dir, music_url, reel_index, voice_reel, use_spotify)
            video_paths = [video_path]
            print(f"2. Assembling music reel with unique video and real song ({lang})...")
            video_clips_handles = [VideoFileClip(vp) for vp in video_paths if os.path.exists(vp)]
            try:
                with concatenate_videoclips(video_clips_handles, method="compose") as background_video, \
                     AudioFileClip(audio_path) as main_audio_clip:
                    looped_audio = afx.audio_loop(main_audio_clip, duration=background_video.duration)
                    background_video.audio = looped_audio
                    if main_audio_clip.duration < background_video.duration:
                        background_video = background_video.subclip(0, main_audio_clip.duration)
                    final_clip = background_video
                    final_video_path = os.path.join(output_dir, f"{safe_topic}_{aspect_ratio}_{lang}_music.mp4")
                    final_clip.write_videofile(
                        final_video_path,
                        codec='libx264',
                        audio_codec='aac',
                        temp_audiofile=os.path.join(temp_dir, 'temp-audio.m4a'),
                        remove_temp=True,
                        threads=2,
                        preset='ultrafast',
                        logger='bar',
                        fps=24,
                        audio_fps=22050
                    )
                print(f"Music reel created successfully: {final_video_path}")
                created_successfully = True
                return final_video_path, song_url
            except Exception as e:
                print(f"[ERROR] Failed to combine video and audio: {e}")
                raise
    finally:
        for clip in video_clips_handles:
            try:
                clip.close()
            except Exception:
                pass
        if created_successfully and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"Cleaned up temporary directory: {temp_dir}")

def generate_blender_script(scene_id, location, characters, audio_files, output_dir):
    """
    Generate a Blender Python script for a scene.
    - location: e.g., 'Japan', 'India', 'China'
    - characters: list of character names (user must provide .glb/.fbx files)
    - audio_files: list of audio file paths for each character's dialogue
    - output_dir: where to save the .py script
    """
    script_path = os.path.join(output_dir, f"scene_{scene_id:02d}_blender.py")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(f"""
import bpy
import os
# --- USER: Set these paths to your downloaded assets ---
CHARACTER_MODELS = {{
{chr(10).join([f'    "{c}": r"/path/to/{c}.glb",' for c in characters])}
}}
ENVIRONMENT_PATH = r"/path/to/{location}_environment.glb"  # Download from Sketchfab/PolyHaven
AUDIO_FILES = {audio_files}
OUTPUT_VIDEO = r"scene_{scene_id:02d}_{location}.mp4"

# --- Load environment ---
bpy.ops.import_scene.gltf(filepath=ENVIRONMENT_PATH)

# --- Load characters ---
for char, model_path in CHARACTER_MODELS.items():
    bpy.ops.import_scene.gltf(filepath=model_path)
    # Optionally, position each character
    # bpy.context.selected_objects[0].location = (...)

# --- Animate characters (placeholder) ---
# You can use Mixamo animations or keyframes here
# For each character, add walk/talk/gesture animation

# --- Sync mouth movement to audio (placeholder) ---
# For each character, add a sound strip and basic mouth movement
# bpy.ops.sequencer.sound_strip_add(filepath=AUDIO_FILES[0], ...)

# --- Camera setup (optional) ---
# bpy.ops.object.camera_add(...)

# --- Render settings ---
bpy.context.scene.render.filepath = OUTPUT_VIDEO
bpy.context.scene.render.image_settings.file_format = 'FFMPEG'
bpy.context.scene.render.ffmpeg.format = 'MPEG4'

# --- Render animation ---
bpy.ops.render.render(animation=True)
""")
    print(f"Blender script generated: {script_path}")
    return script_path

PEXELS_API_KEY = os.getenv('PEXELS_API_KEY', 'GOweee7vdaLSXHx4tuWMP6rH1iylqn7oVkd0nlSBIfxzSWKL6D1IOBPi')

COUNTRY_BG_QUERIES = {
    'Japan': 'japan city street anime',
    'India': 'india city street',
    'China': 'china city street',
}

def download_backgrounds(output_dir='backgrounds'):
    os.makedirs(output_dir, exist_ok=True)
    headers = {'Authorization': PEXELS_API_KEY}
    for country, query in COUNTRY_BG_QUERIES.items():
        url = f'https://api.pexels.com/v1/search?query={query}&per_page=1&orientation=landscape'
        try:
            r = requests.get(url, headers=headers)
            r.raise_for_status()
            data = r.json()
            if data['photos']:
                img_url = data['photos'][0]['src']['large']
                img_path = os.path.join(output_dir, f'{country}.jpg')
                img_data = requests.get(img_url).content
                with open(img_path, 'wb') as f:
                    f.write(img_data)
                print(f"Downloaded background for {country}: {img_path}")
            else:
                print(f"No background found for {country}")
        except Exception as e:
            print(f"Failed to download background for {country}: {e}")
    return {country: os.path.join(output_dir, f'{country}.jpg') for country in COUNTRY_BG_QUERIES}

# Call this at the start of your pipeline to ensure backgrounds are available
# backgrounds = download_backgrounds()

# Add a random delay after each upload (to be called from main.py)
def random_upload_delay():
    delay = random.randint(300, 420)  # 5 to 7 minutes
    print(f"[DELAY] Sleeping for {delay} seconds to mimic human behavior...")
    time.sleep(delay)

if __name__ == '__main__':
    from dotenv import load_dotenv
    load_dotenv()
    
    async def run_test():
        output_folder = "test_videos"
        os.makedirs(output_folder, exist_ok=True)
        try:
            await create_video("The Future of Renewable Energy", 60, "portrait", output_folder)
        except Exception as e:
            print(f"Test failed: {e}")

    asyncio.run(run_test())
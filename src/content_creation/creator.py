import os
import shutil
import asyncio
import requests
import textwrap
import random
import time
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, TextClip, ImageClip
)
import moviepy.audio.fx.all as afx
from src.content_creation.script_generator import generate_script, parse_script_to_dialogues
from src.content_creation.voice_generator import generate_realistic_voice, generate_multi_voice

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

async def create_video(topic: str, duration: int, aspect_ratio: str, output_dir: str = "."):
    """
    Creates a high-quality video, storing all intermediate files in a sub-folder of the output directory.
    If topic is anime/movie, creates a simple animated movie with multiple character voices and placeholder images.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        raise ValueError("PEXELS_API_KEY environment variable not set.")

    temp_dir = os.path.join(output_dir, f"temp_{topic.replace(' ', '_')}_{random.randint(1000, 9999)}")
    os.makedirs(temp_dir, exist_ok=True)
    
    video_clips_handles = []
    created_successfully = False
    
    try:
        audio_path = os.path.join(temp_dir, "voiceover.mp3")
        music_path = os.path.join(temp_dir, "music.mp3")
        
        print(f"\n1. Generating {int(duration/60)} min script for '{topic}'...")
        script = generate_script(topic, duration)
        # --- Anime/Movie special handling ---
        if 'anime' in topic.lower() or 'movie' in topic.lower():
            print("Detected anime/movie topic. Generating multi-character voices and animation...")
            dialogues = parse_script_to_dialogues(script)
            audio_paths = generate_multi_voice(dialogues, temp_dir)
            # Use placeholder character images (free, local or from the web)
            character_images = {}
            for character, _ in dialogues:
                if character not in character_images:
                    # Download or use a local placeholder image for each character
                    img_path = os.path.join(temp_dir, f"{character.replace(' ', '_')}.png")
                    if not os.path.exists(img_path):
                        # Download a free anime avatar (placeholder)
                        url = "https://api.multiavatar.com/" + character + ".png"
                        try:
                            r = requests.get(url)
                            with open(img_path, 'wb') as f:
                                f.write(r.content)
                        except Exception:
                            # fallback to a solid color image
                            from PIL import Image
                            img = Image.new('RGB', (512, 512), (random.randint(0,255), random.randint(0,255), random.randint(0,255)))
                            img.save(img_path)
                    character_images[character] = img_path
            # Create a video clip for each dialogue line
            clips = []
            for idx, ((character, line), audio_file) in enumerate(zip(dialogues, audio_paths)):
                img_path = character_images[character]
                audio_clip = AudioFileClip(audio_file)
                img_clip = ImageClip(img_path).set_duration(audio_clip.duration).resize(height=720)
                img_clip = img_clip.set_audio(audio_clip)
                # Add character name as text overlay
                txt_clip = TextClip(character, fontsize=48, color='white', bg_color='black', size=(img_clip.w, 60)).set_duration(audio_clip.duration)
                txt_clip = txt_clip.set_position(('center', 'bottom'))
                final_clip = CompositeVideoClip([img_clip, txt_clip])
                clips.append(final_clip)
            final_video = concatenate_videoclips(clips, method="compose")
            final_video_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}_{aspect_ratio}_ANIME.mp4")
            final_video.write_videofile(
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
            print(f"Anime movie created successfully: {final_video_path}")
            created_successfully = True
            return final_video_path
        # --- END Anime/Movie special handling ---
        
        generate_realistic_voice(script, audio_path)

        # --- FIX: Wait for the audio file to be ready ---
        for _ in range(10): # Try for 5 seconds
            if os.path.exists(audio_path) and os.path.getsize(audio_path) > 0:
                break
            time.sleep(0.5)
        else:
            raise FileNotFoundError(f"Audio file was not created or is empty: {audio_path}")
        # --- END FIX ---
        
        with AudioFileClip(audio_path) as voiceover_clip:
            actual_duration = voiceover_clip.duration

        print("2. Downloading background videos and music...")
        orientation = 'portrait' if aspect_ratio == 'portrait' else 'landscape'
        
        # Limit the number of clips to download.
        num_clips = 3 if aspect_ratio == 'portrait' else 5
        
        search_url = f"https://api.pexels.com/videos/search?query={topic}&per_page={num_clips}&orientation={orientation}"
        
        response = requests.get(search_url, headers={'Authorization': api_key})
        response.raise_for_status()
        videos_json = response.json().get('videos', [])
        if not videos_json:
            raise ValueError(f"No videos found for topic: {topic}")

        download_tasks = []
        video_paths = []
        for i, video_data in enumerate(videos_json):
            video_url = next((f['link'] for f in video_data['video_files'] if f['quality'] == 'hd'), video_data['video_files'][0]['link'])
            video_path = os.path.join(temp_dir, f"video_{i}.mp4")
            video_paths.append(video_path)
            download_tasks.append(download_media(video_url, video_path))

        music_url = "https://www.bensound.com/bensound-music/bensound-creativeminds.mp3"
        download_tasks.append(download_media(music_url, music_path))
        
        await asyncio.gather(*download_tasks)

        print("3. Assembling video with transitions and effects...")
        
        video_clips_handles = [VideoFileClip(vp) for vp in video_paths if os.path.exists(vp)]
        
        with concatenate_videoclips(video_clips_handles, method="compose") as background_video, \
             AudioFileClip(music_path).volumex(0.1) as music_clip, \
             AudioFileClip(audio_path) as voiceover_clip_handle:

            looped_music = afx.audio_loop(music_clip, duration=voiceover_clip_handle.duration)

            final_audio = CompositeAudioClip([voiceover_clip_handle, looped_music])
            background_video.audio = final_audio
            if voiceover_clip_handle.duration < background_video.duration:
                background_video = background_video.subclip(0, voiceover_clip_handle.duration)

            # Subtitles are disabled to fix the ImageMagick error.
            final_clip = background_video
            
            final_video_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}_{aspect_ratio}.mp4")
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
        
        print(f"Video created successfully: {final_video_path}")
        created_successfully = True
        return final_video_path

    finally:
        # This block ensures all file handles are closed, even if an error occurred.
        for clip in video_clips_handles:
            try:
                clip.close()
            except Exception:
                pass
        
        # Only delete the temp folder if the video was created successfully.
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
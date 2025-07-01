import os
import shutil
import asyncio
import requests
import textwrap
import random
import time
from moviepy.editor import (
    VideoFileClip, AudioFileClip, CompositeVideoClip, CompositeAudioClip,
    concatenate_videoclips, TextClip
)
import moviepy.audio.fx.all as afx
from src.content_creation.script_generator import generate_script
from src.content_creation.voice_generator import generate_realistic_voice

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
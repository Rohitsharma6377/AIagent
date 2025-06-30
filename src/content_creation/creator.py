import os
import asyncio
import requests
import subprocess
import tempfile
from gtts import gTTS
from imageio_ffmpeg import get_ffmpeg_exe
from src.content_creation.script_generator import generate_script

async def create_video_ffmpeg(topic, duration, aspect_ratio, output_dir=".", language='en'):
    """
    Creates a video about a given topic using FFmpeg.

    Args:
        topic (str): The topic of the video.
        duration (int): The target duration of the video in seconds.
        aspect_ratio (str): 'landscape' (16:9) or 'portrait' (9:16).
        output_dir (str): The directory to save the output files.
        language (str): Language for TTS ('en' for English, 'hi' for Hindi)

    Returns:
        str: The path to the created video file, or None if failed.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("Error: PEXELS_API_KEY environment variable not set.")
        return None

    # Create temporary directory for intermediate files
    with tempfile.TemporaryDirectory() as temp_dir:
        audio_path = os.path.join(temp_dir, "voiceover.mp3")
        video_path = os.path.join(temp_dir, "background.mp4")
        music_path = os.path.join(temp_dir, "background_music.mp3")
        mixed_audio_path = os.path.join(temp_dir, "mixed_audio.mp3")
        final_video_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}_{aspect_ratio}_{language}.mp4")

        # 1. Generate Audio using AI Script
        print("Generating AI script for the audio...")
        script = generate_script(topic, duration, language)
        
        print("Generating audio from script...")
        try:
            tts = gTTS(text=script, lang=language, slow=False)
            tts.save(audio_path)
        except Exception as e:
            print(f"Failed to generate audio: {e}")
            return None

        # 2. Download Background Video
        print(f"Finding {aspect_ratio} background video...")
        try:
            # Convert aspect ratio to Pexels format
            orientation = 'landscape' if aspect_ratio == 'landscape' else 'portrait'
            
            # Search terms for more engaging videos
            search_terms = {
                'en': ['cinematic', 'beautiful', 'aesthetic'],
                'hi': ['indian', 'beautiful', 'cinematic']
            }
            
            # Add relevant search terms based on language
            enhanced_topic = f"{topic} {' '.join(search_terms[language])}"
            
            # Search for videos using Pexels API
            headers = {'Authorization': api_key}
            search_url = f'https://api.pexels.com/videos/search?query={enhanced_topic}&per_page=1&orientation={orientation}'
            
            response = requests.get(search_url, headers=headers)
            response.raise_for_status()
            
            videos = response.json().get('videos', [])
            if not videos:
                print(f"No {aspect_ratio} videos found for topic: {enhanced_topic}")
                return None
            
            # Get the video URL (prefer HD quality if available)
            video = videos[0]
            video_files = video.get('video_files', [])
            video_url = next(
                (f['link'] for f in video_files if f.get('quality') == 'hd'),
                video_files[0]['link'] if video_files else None
            )
            
            if not video_url:
                print("No suitable video file found.")
                return None
            
            # Download the video
            print(f"Downloading video from {video_url}...")
            with requests.get(video_url, stream=True) as r:
                r.raise_for_status()
                with open(video_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)

            # Download background music (you can add your own royalty-free music)
            # For now, we'll create a silent audio file as a placeholder
            ffmpeg_exe = get_ffmpeg_exe()
            subprocess.run([
                ffmpeg_exe,
                '-f', 'lavfi',
                '-i', 'anullsrc=r=44100:cl=stereo',
                '-t', '10',
                '-q:a', '0',
                '-acodec', 'libmp3lame',
                music_path
            ], check=True, capture_output=True)

            # Mix voiceover with background music
            subprocess.run([
                ffmpeg_exe,
                '-i', audio_path,
                '-i', music_path,
                '-filter_complex',
                '[1:a]volume=0.2[music];[0:a][music]amix=duration=longest',
                '-c:a', 'libmp3lame',
                mixed_audio_path
            ], check=True, capture_output=True)

        except Exception as e:
            print(f"Failed to prepare media: {e}")
            return None

        # 3. Create final video with FFmpeg
        print("Creating final video with FFmpeg...")
        try:
            # Add video effects and combine with mixed audio
            cmd = [
                ffmpeg_exe,
                '-stream_loop', '-1',          # Loop the video input
                '-i', video_path,
                '-i', mixed_audio_path,
                '-vf', 'scale=w=-2:h=1920,fps=30',  # Scale video maintaining aspect ratio
                '-c:v', 'libx264',
                '-preset', 'slow',             # Better quality
                '-crf', '22',                  # High quality (lower value = higher quality)
                '-c:a', 'aac',
                '-b:a', '192k',               # High quality audio
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-t', str(duration),           # Set total duration
                '-shortest',
                final_video_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"Video created successfully: {final_video_path}")
            return final_video_path

        except subprocess.CalledProcessError as e:
            print(f"Failed to create video with FFmpeg. Error: {e.stderr}")
            return None
        except Exception as e:
            print(f"An unexpected error occurred during video creation: {e}")
            return None

if __name__ == '__main__':
    # For direct testing
    async def test_creator():
        from dotenv import load_dotenv
        load_dotenv()
        if not os.getenv("PEXELS_API_KEY"):
            print("Please set the PEXELS_API_KEY environment variable to test.")
        else:
            print("\nCreating English Landscape Video...")
            await create_video_ffmpeg("Technology Trends", 10, "landscape", language='en')
            
            print("\nCreating Hindi Portrait Video...")
            await create_video_ffmpeg("प्रौद्योगिकी का भविष्य", 30, "portrait", language='hi')

    asyncio.run(test_creator()) 
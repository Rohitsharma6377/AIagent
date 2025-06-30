import os
import asyncio
import requests
from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeVideoClip, TextClip
from pexels_api import API

async def create_video(topic, output_dir="."):
    """
    Creates a video about a given topic.
    """
    api_key = os.getenv("PEXELS_API_KEY")
    if not api_key:
        print("Error: PEXELS_API_KEY environment variable not set.")
        return None

    api = API(api_key)
    audio_path = os.path.join(output_dir, "voiceover.mp3")
    video_path = os.path.join(output_dir, "background.mp4")

    print("Generating audio...")
    try:
        tts = gTTS(f"Here is a short video about {topic}", lang='en')
        tts.save(audio_path)
    except Exception as e:
        print(f"Failed to generate audio: {e}")
        return None

    print("Finding background video...")
    try:
        api.search_videos(topic, page=1, results_per_page=1, orientation='landscape')
        videos = api.get_entries()
        if not videos:
            print(f"No videos found for topic: {topic}")
            return None
        
        video_url = next((f.link for f in videos[0].video_files if f.quality == 'hd'), videos[0].video_files[0].link)
        
        with requests.get(video_url, stream=True) as r:
            r.raise_for_status()
            with open(video_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192): 
                    f.write(chunk)
    except Exception as e:
        print(f"Failed to download video: {e}")
        return None

    print("Creating final video...")
    try:
        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        if audio_clip.duration > video_clip.duration:
            audio_clip = audio_clip.subclip(0, video_clip.duration)
        else:
            video_clip = video_clip.subclip(0, audio_clip.duration)

        final_clip = video_clip.set_audio(audio_clip)

        txt_clip = TextClip(topic, fontsize=70, color='white', font='Arial-Bold', stroke_color='black', stroke_width=2)
        txt_clip = txt_clip.set_pos('center').set_duration(final_clip.duration)
        
        final_video = CompositeVideoClip([final_clip, txt_clip])
        
        output_video_path = os.path.join(output_dir, f"{topic.replace(' ', '_')}.mp4")
        final_video.write_videofile(output_video_path, codec="libx264", audio_codec="aac", threads=4)
        
        print(f"Video created successfully: {output_video_path}")
        return output_video_path
        
    except Exception as e:
        print(f"Failed to create video: {e}")
        return None
    finally:
        if os.path.exists(audio_path): os.remove(audio_path)
        if os.path.exists(video_path): os.remove(video_path)


async def main():
    """
    Main function to run the AI agent.
    """
    topic = "The Future of Artificial Intelligence"
    print(f"Starting video creation for topic: {topic}")
    
    if not os.getenv("PEXELS_API_KEY"):
        print("\nPlease set the PEXELS_API_KEY environment variable.")
        print("You can get a free key from: https://www.pexels.com/api/")
        print("Then run 'setx PEXELS_API_KEY \"YOUR_KEY\"' in your terminal and restart it.")
        return

    video_path = await create_video(topic)

    if video_path:
        print(f"\nVideo generation complete: {video_path}")
    else:
        print("\nVideo generation failed.")


if __name__ == "__main__":
    asyncio.run(main())

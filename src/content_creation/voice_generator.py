import os
from dotenv import load_dotenv
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from gtts import gTTS

def generate_realistic_voice(text: str, output_path: str):
    """
    Generate voice using ElevenLabs API. If it fails (e.g., quota exceeded),
    fall back to gTTS.
    
    Args:
        text (str): Text to convert to speech.
        output_path (str): The path to save the generated audio file.
    """
    load_dotenv()
    api_key = os.getenv('ELEVEN_LABS_API_KEY')
    
    # --- Attempt 1: Use ElevenLabs for high-quality voice ---
    if api_key:
        print("Attempting to generate voice with ElevenLabs...")
        try:
            client = ElevenLabs(api_key=api_key)
            hindi_voice_id = "AZnzlk1XvdvUeBnXmlld" 

            audio_stream = client.text_to_speech.stream(
                text=text,
                voice_id=hindi_voice_id,
                model_id="eleven_multilingual_v2"
            )
            
            save(audio_stream, output_path)
            print(f"Successfully generated voice with ElevenLabs and saved to {output_path}")
            return # Success, exit the function
        except Exception as e:
            print(f"ElevenLabs API failed: {e}")
            if 'quota_exceeded' in str(e).lower():
                print("Your ElevenLabs quota is exceeded. Falling back to a standard voice.")
            else:
                print("An unknown error occurred with ElevenLabs. Falling back to a standard voice.")
    else:
        print("ELEVEN_LABS_API_KEY not found. Using standard voice.")

    # --- Attempt 2: Fallback to gTTS ---
    try:
        print("Generating voice with gTTS as a fallback...")
        # Using a specific TLD can help avoid regional rate-limiting issues.
        tts = gTTS(text=text, lang='hi', tld='co.in', slow=False)
        tts.save(output_path)
        print(f"Successfully generated voice with gTTS and saved to {output_path}")
    except Exception as e:
        print(f"gTTS also failed: {e}")
        raise # If both fail, the program should stop

if __name__ == "__main__":
    load_dotenv()
    
    test_text_hindi = "नमस्ते! आज हम आर्टिफिशियल इंटेलिजेंस और हमारे भविष्य पर इसके प्रभाव के बारे में बात करेंगे।"
    output_file = "test_hindi_voice.mp3"
    
    print("\nTesting Hindi voice generation...")
    try:
        generate_realistic_voice(test_text_hindi, output_file)
        print(f"Test voice file created: {output_file}")
    except ValueError as e:
        print(e)

import os
from dotenv import load_dotenv
from elevenlabs import save
from elevenlabs.client import ElevenLabs
from gtts import gTTS
import random

def generate_realistic_voice(text: str, output_path: str, voice_id: str = None):
    """
    Generate voice using ElevenLabs API. If it fails (e.g., quota exceeded),
    fall back to gTTS.
    
    Args:
        text (str): Text to convert to speech.
        output_path (str): The path to save the generated audio file.
        voice_id (str): Optional, for multi-character support.
    """
    load_dotenv()
    api_key = os.getenv('ELEVEN_LABS_API_KEY')
    
    # --- Attempt 1: Use ElevenLabs for high-quality voice ---
    if api_key:
        print(f"Attempting to generate voice with ElevenLabs{' (voice_id: ' + str(voice_id) + ')' if voice_id else ''}...")
        try:
            client = ElevenLabs(api_key=api_key)
            hindi_voice_id = voice_id or "AZnzlk1XvdvUeBnXmlld" 

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
        print(f"Generating voice with gTTS as a fallback{' (voice_id: ' + str(voice_id) + ')' if voice_id else ''}...")
        # Use different tld or slow for different characters for variety
        tlds = ['co.in', 'com', 'co.uk', 'ca', 'com.au']
        tld = random.choice(tlds) if voice_id else 'co.in'
        tts = gTTS(text=text, lang='hi', tld=tld, slow=False)
        tts.save(output_path)
        print(f"Successfully generated voice with gTTS and saved to {output_path}")
    except Exception as e:
        print(f"gTTS also failed: {e}")
        raise # If both fail, the program should stop

def generate_multi_voice(dialogues, output_dir):
    """
    Given a list of (character, dialogue), generate separate audio files for each line,
    using different voices for each character. Returns a list of audio file paths in order.
    """
    # Assign a unique voice_id or tld to each character
    character_voice_map = {}
    voice_ids = [
        "AZnzlk1XvdvUeBnXmlld",  # ElevenLabs default
        "EXAVITQu4vr4xnSDxMaL",  # ElevenLabs male
        "21m00Tcm4TlvDq8ikWAM",  # ElevenLabs female
        "ErXwobaYiN019PkySvjV",  # ElevenLabs deep
        "TxGEqnHWrfWFTfGW9XjX",  # ElevenLabs young
    ]
    tlds = ['co.in', 'com', 'co.uk', 'ca', 'com.au']
    audio_paths = []
    for idx, (character, line) in enumerate(dialogues):
        if character not in character_voice_map:
            # Assign a voice_id and tld to each character
            character_voice_map[character] = {
                'voice_id': voice_ids[len(character_voice_map) % len(voice_ids)],
                'tld': tlds[len(character_voice_map) % len(tlds)]
            }
        voice_id = character_voice_map[character]['voice_id']
        tld = character_voice_map[character]['tld']
        audio_path = os.path.join(output_dir, f"{idx:02d}_{character.replace(' ', '_')}.mp3")
        try:
            # Try ElevenLabs first, fallback to gTTS with tld for variety
            generate_realistic_voice(line, audio_path, voice_id=voice_id)
        except Exception:
            # Fallback to gTTS with tld
            print(f"Falling back to gTTS for {character}...")
            tts = gTTS(text=line, lang='hi', tld=tld, slow=False)
            tts.save(audio_path)
        audio_paths.append(audio_path)
    return audio_paths

if __name__ == "__main__":
    load_dotenv()
    
    test_dialogues = [
        ("Rohan", "क्या तुमने आज का होमवर्क किया?"),
        ("Priya", "हाँ, लेकिन मुझे गणित में थोड़ी परेशानी हुई।"),
        ("Sensei", "कोई बात नहीं, मैं तुम्हारी मदद करूंगा।")
    ]
    output_dir = "test_voices"
    os.makedirs(output_dir, exist_ok=True)
    print("\nTesting multi-voice generation...")
    try:
        paths = generate_multi_voice(test_dialogues, output_dir)
        print(f"Generated files: {paths}")
    except Exception as e:
        print(e)

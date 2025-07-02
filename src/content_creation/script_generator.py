import os
import google.generativeai as genai
from dotenv import load_dotenv
import requests
import re

# Helper for Hugging Face Inference API
HF_API_URL = "https://api-inference.huggingface.co/models/google/flan-t5-base"
def generate_script_hf(prompt: str) -> str:
    headers = {"Accept": "application/json"}
    # Optionally, add 'Authorization': f'Bearer {os.getenv("HF_API_KEY")}' if you have a key
    payload = {"inputs": prompt}
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    data = response.json()
    # Hugging Face returns a list of dicts with 'generated_text'
    if isinstance(data, list) and 'generated_text' in data[0]:
        return data[0]['generated_text'].strip()
    elif isinstance(data, dict) and 'error' in data:
        raise RuntimeError(f"Hugging Face API error: {data['error']}")
    else:
        return str(data)

def parse_script_to_dialogues(script: str):
    """
    Parses a script into a list of (character, dialogue) tuples.
    Assumes lines are in the format: CHARACTER: dialogue
    """
    dialogues = []
    for line in script.splitlines():
        match = re.match(r"([A-Za-z0-9_\- ]+):\s*(.+)", line)
        if match:
            character, dialogue = match.groups()
            dialogues.append((character.strip(), dialogue.strip()))
    return dialogues

def generate_script(topic: str, duration: int) -> str:
    """
    Generate a detailed script in Hindi for a video of a specific duration.
    Tries Gemini API first, then falls back to Hugging Face Inference API (flan-t5-base).

    Args:
        topic (str): The topic for the script (can be in English).
        duration (int): The target duration of the video in seconds.

    Returns:
        str: The generated script in Hindi.
    """
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    # Approximate words per second for a clear speaking pace.
    words_per_second = 2.5
    target_words = int(duration * words_per_second)

    # If anime/movie, generate a multi-character script
    if 'anime' in topic.lower() or 'movie' in topic.lower():
        prompt = f"""
        Write a detailed script for a short animated movie in Hindi with at least 3 named characters. Each line should be in the format: CHARACTER: dialogue. The script should be about '{topic}'.
        The script should include:
        - An engaging introduction
        - Dialogues between characters (at least 3 characters, e.g., Rohan, Priya, Sensei)
        - A conflict and resolution
        - A conclusion
        - Each character should have a unique speaking style
        - The script should be about {target_words} words
        - Only output the script, no explanation
        """
    else:
        prompt = f"""
        आपको एक {int(duration / 60)} मिनट के यूट्यूब वीडियो के लिए एक विस्तृत और आकर्षक स्क्रिप्ट लिखनी है।
        
        विषय: "{topic}"
        
        भाषा: केवल हिंदी।
        
        कुल शब्द: लगभग {target_words} शब्द।

        स्क्रिप्ट की संरचना इस प्रकार होनी चाहिए:
        1.  **आकर्षक परिचय (Engaging Hook):** 15-20 सेकंड। दर्शकों का ध्यान खींचने के लिए एक दिलचस्प तथ्य, सवाल या कहानी से शुरुआत करें।
        2.  **मुख्य सामग्री (Main Content):** विषय को 3-4 मुख्य भागों में विभाजित करें। प्रत्येक भाग को विस्तार से समझाएं, उदाहरण दें और इसे सरल और समझने योग्य भाषा में प्रस्तुत करें।
        3.  **निष्कर्ष (Conclusion):** 30 सेकंड। मुख्य बिंदुओं को सारांशित करें और दर्शकों को एक कॉल-टू-एक्शन दें (जैसे 'लाइक करें', 'सब्सक्राइब करें') या एक विचारोत्तेजक प्रश्न पूछें।

        यह सुनिश्चित करें कि स्क्रिप्ट स्वाभाविक और बातचीत की शैली में हो। जटिल शब्दों से बचें।
        कृपया केवल अंतिम स्क्रिप्ट का हिंदी टेक्स्ट ही प्रदान करें।
        """

    # Try Gemini API first
    if api_key:
        try:
            response = model.generate_content(prompt)
            script = response.text.strip()
            print(f"[generate_script] Used Gemini API for topic: {topic}")
            return script
        except Exception as e:
            print(f"[generate_script] Gemini API failed: {e}\nFalling back to Hugging Face Inference API.")
    else:
        print("[generate_script] GOOGLE_API_KEY not set. Using Hugging Face Inference API.")
    # Fallback: Hugging Face
    try:
        script = generate_script_hf(prompt)
        print(f"[generate_script] Used Hugging Face Inference API for topic: {topic}")
        return script
    except Exception as e:
        print(f"[generate_script] Hugging Face API failed: {e}")
        raise RuntimeError("Both Gemini and Hugging Face script generation failed.")

if __name__ == "__main__":
    load_dotenv()
    print("\nTesting 1-minute Hindi Script Generation:")
    print("-" * 50)
    try:
        script = generate_script("Anime Movie: Magical Quest", 120)
        print(script)
        print("\nParsed Dialogues:")
        for char, line in parse_script_to_dialogues(script):
            print(f"{char}: {line}")
    except Exception as e:
        print(e)

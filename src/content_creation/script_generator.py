import os
import google.generativeai as genai
from dotenv import load_dotenv

def generate_script(topic, duration, language='en'):
    """
    Generate a script about a topic using Google's Generative AI.
    
    Args:
        topic (str): The topic to generate content about
        duration (int): Target duration in seconds
        language (str): 'en' for English, 'hi' for Hindi
    
    Returns:
        str: The generated script
    """
    load_dotenv()
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("Error: GOOGLE_API_KEY environment variable not set")
        return "Sample script for testing."

    # Configure the generative AI model
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    # Calculate approximate word count based on duration
    # Average speaking speed: ~150 words per minute
    target_words = (duration / 60) * 150

    # Define prompts based on language
    prompts = {
        'en': f"""Write an engaging and conversational script about {topic}.
                The script should be approximately {int(target_words)} words long.
                Make it informative yet casual, like you're talking to a friend.
                Focus on the most interesting aspects and recent developments.
                Don't use complex words or technical jargon.
                Don't mention dates or statistics that could become outdated.
                End with a thought-provoking conclusion.""",
        
        'hi': f""""{topic}" के बारे में एक आकर्षक और बातचीत की शैली में स्क्रिप्ट लिखें।
                स्क्रिप्ट लगभग {int(target_words)} शब्दों की होनी चाहिए।
                इसे जानकारीपूर्ण लेकिन सरल रखें, जैसे आप किसी दोस्त से बात कर रहे हैं।
                सबसे दिलचस्प पहलुओं और हाल के विकास पर ध्यान दें।
                जटिल शब्दों या तकनीकी शब्दजाल का उपयोग न करें।
                ऐसी तारीखें या आंकड़े न दें जो पुराने हो सकते हैं।
                एक विचारोत्तेजक निष्कर्ष के साथ समाप्त करें।"""
    }

    try:
        # Generate the script
        response = model.generate_content(prompts[language])
        script = response.text.strip()
        
        print(f"Successfully generated script for topic: {topic}")
        return script
    except Exception as e:
        print(f"Error generating script: {e}")
        return "Error generating script. Using fallback content."

if __name__ == "__main__":
    # Test script generation
    from dotenv import load_dotenv
    load_dotenv()
    
    print("\nTesting English Script Generation:")
    print("-" * 50)
    print(generate_script("Future of AI", 60, 'en'))
    
    print("\nTesting Hindi Script Generation:")
    print("-" * 50)
    print(generate_script("आर्टिफिशियल इंटेलिजेंस का भविष्य", 60, 'hi'))

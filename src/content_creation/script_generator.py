import os
import google.generativeai as genai
from dotenv import load_dotenv

def generate_script(topic: str, duration: int) -> str:
    """
    Generate a detailed script in Hindi for a video of a specific duration.

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

    try:
        response = model.generate_content(prompt)
        script = response.text.strip()
        print(f"Successfully generated {int(duration/60)}-minute script for topic: {topic}")
        return script
    except Exception as e:
        print(f"Error generating script: {e}")
        raise

if __name__ == "__main__":
    load_dotenv()
    print("\nTesting 1-minute Hindi Script Generation:")
    print("-" * 50)
    try:
        print(generate_script("Artificial Intelligence", 60))
    except Exception as e:
        print(e)

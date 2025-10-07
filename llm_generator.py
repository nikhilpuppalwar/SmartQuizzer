import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load .env variables (like GEMINI_API_KEY)
load_dotenv()

# Configure Gemini API using the environment variable
try:
    # Use the API key from the environment
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
except Exception as e:
    # Print a warning if configuration fails but allow the function to be defined
    print(f"Warning: Gemini API configuration failed. Ensure GEMINI_API_KEY is set. Error: {e}")


def generate_questions(name, topic, skill_level, num_questions, class_level=None):
    """
    Generate multiple-choice quiz questions using Gemini API.
    It constructs a prompt and returns the raw JSON string response.
    The code is now simplified to work with older SDK versions like 0.8.5 by removing
    unsupported arguments (config, system_instruction).
    """
    class_info = f"for a {class_level} level student" if class_level and class_level != "None" else ""
    
    # Relying on a very strong prompt to enforce JSON output structure.
    user_query = f"""
    You are an expert quiz generator. Your task is to generate {num_questions} multiple-choice quiz 
    questions on the topic '{topic}' {class_info}.
    
    The difficulty MUST match the '{skill_level}' skill level.
    Each question MUST have 4 options and clearly indicate the correct answer.
    
    YOU MUST RESPOND ONLY with a valid JSON array of objects. 
    DO NOT include any explanation, preamble, or markdown formatting (like ```json) before or after the JSON.
    
    The JSON array MUST strictly follow this exact structure:
    [
      {{"question": "...", "options": ["Option A", "Option B", "Option C", "Option D"], "answer": "The correct option text"}}
    ]
    """

    # Using the recommended and generally compatible model name
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    try:
        # Simple content generation call, compatible with SDK 0.8.5
        response = model.generate_content(
            user_query 
        )
        
        # The response text should be the raw JSON string
        return response.text
        
    except Exception as e:
        # Print the error for debugging purposes in the Streamlit console
        print(f"API Call Error: {e}") 
        return None

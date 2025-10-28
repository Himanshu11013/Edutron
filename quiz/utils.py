import google.generativeai as genai
import requests
import os
import time
import socket
import json
from dotenv import load_dotenv
load_dotenv()

def is_proxy_needed():
    """Check if we're likely in the hostel network that needs a proxy"""
    # First check if the user explicitly wants to use a proxy via flag file
    if os.path.exists("use_proxy.flag"):
        return True
        
    try:
        # Try to get hostname and IP address
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        
        # Check if we're in a specific network that requires proxy
        return ip.startswith("172.31.")
    except Exception as e:
        print(f"Error detecting network: {e}")
        # If any error occurs, default to no proxy
        return False

def configure_api(force_proxy=None):
    """
    Configure the Gemini API with or without proxy based on the network
    
    Args:
        force_proxy: Override automatic detection. 
                    True to force using proxy, 
                    False to force not using proxy,
                    None to use automatic detection
    """
    # Always configure with the API key
    api_config = {
        "api_key": os.getenv("GEMINI_API_KEY"),
        "transport": "rest",
    }
    
    # Determine if proxy is needed
    use_proxy = force_proxy if force_proxy is not None else is_proxy_needed()
    
    if use_proxy:
        print("Configuring with proxy")
        # Set proxy for environment
        os.environ["HTTP_PROXY"] = "http://172.31.2.4:8080"
        os.environ["HTTPS_PROXY"] = "http://172.31.2.4:8080"
    else:
        print("Configuring without proxy")
        # Clear any proxy settings that might be lingering
        if "HTTP_PROXY" in os.environ:
            del os.environ["HTTP_PROXY"]
        if "HTTPS_PROXY" in os.environ:
            del os.environ["HTTPS_PROXY"]
    
    # Configure the API
    genai.configure(**api_config)

def extract_json_from_response(text):
    """Extract valid JSON from the API response, handling different formats"""
    # Try to parse directly first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # Try to extract JSON from markdown code blocks
    try:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
        if match:
            return json.loads(match.group(1).strip())
    except (json.JSONDecodeError, AttributeError, IndexError):
        pass
    
    # Try to find JSON array in the text
    try:
        match = re.search(r'(\[\s*\{.*\}\s*\])', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except (json.JSONDecodeError, AttributeError, IndexError):
        pass
    
    # If all else fails, return empty list
    print("Could not extract valid JSON from response")
    return []

def generate_questions(topic, numQuestions, difficulty):
    """
    Generate quiz questions using the Gemini API with enhanced error handling and logging.
    
    Args:
        topic (str): The topic for the quiz questions
        numQuestions (int): Number of questions to generate
        difficulty (str): Difficulty level (Beginner/Intermediate/Advanced)
        
    Returns:
        str: JSON string containing the generated questions
    """
    print(f"\n{'='*80}\nStarting question generation...")
    print(f"Topic: {topic}")
    print(f"Number of questions: {numQuestions}")
    print(f"Difficulty: {difficulty}")
    print(f"GEMINI_API_KEY: {'Set' if os.getenv('GEMINI_API_KEY') else 'NOT SET'}")
    
    # Input validation
    if not topic or not isinstance(topic, str):
        print("Error: Invalid topic provided")
        return "[]"
        
    try:
        numQuestions = int(numQuestions)
        if numQuestions <= 0 or numQuestions > 20:  # Sanity check
            print(f"Warning: Number of questions adjusted from {numQuestions} to 5")
            numQuestions = 5
    except (ValueError, TypeError):
        print("Warning: Invalid numQuestions, using default of 5")
        numQuestions = 5
    
    prompt = f"""
    Generate exactly {numQuestions} multiple-choice quiz questions on "{topic}" with these requirements:
    
    - Difficulty: {difficulty} (Beginner/Intermediate/Advanced)
    - Each question must have:
      * Clear, concise question text
      * 4 options (a, b, c, d)
      * Exactly one correct answer
      * 2-3 relevant tags
      * A helpful hint
      * A detailed solution
    - Format options as: {{"a": "Option 1", "b": "Option 2", "c": "Option 3", "d": "Option 4"}}
    - Return ONLY a valid JSON array of question objects
    - If the topic is inappropriate, return an empty array []
    
    Example format for each question:
    {{
        "question": "What is the capital of France?",
        "options": {{"a": "Berlin", "b": "Madrid", "c": "Paris", "d": "Lisbon"}},
        "difficulty": "{difficulty}",
        "tags": ["geography", "capital cities"],
        "correct_answer": "c",
        "attempted_option": "",
        "hints": "Famous for Eiffel Tower",
        "solution": "Paris is the capital of France, known for the Eiffel Tower."
    }}
    """
    
    print("\nPrompt sent to Gemini API:")
    print("-" * 40)
    print(prompt)
    print("-" * 40)
    
    strategies = [
        {"name": "Auto detection", "force_proxy": None},
        {"name": "With proxy", "force_proxy": True},
        {"name": "Without proxy", "force_proxy": False}
    ]
    
    for strategy in strategies:        
        try:
            print(f"\nTrying {strategy['name']} strategy...")
            configure_api(force_proxy=strategy["force_proxy"])
            
            # Verify API key is set
            if not os.getenv("GEMINI_API_KEY"):
                print("Error: GEMINI_API_KEY environment variable not set")
                continue
                
            # Create model and generate content
            print("Initializing Gemini model...")
            model = genai.GenerativeModel("gemini-2.0-flash")
            
            print("Sending request to Gemini API...")
            start_time = time.time()
            try:
                response = model.generate_content(prompt, stream=False)
                print(f"Received response in {time.time() - start_time:.2f} seconds")
                # For non-streaming, response.text is the full output
                text = response.text if hasattr(response, 'text') else str(response)
                print(f"Raw response length: {len(text)} characters")
                print("First 500 chars of response:")
                print("-" * 40)
                print(text[:500])
                if len(text) > 500:
                    print("...")
                print("-" * 40)
            except Exception as api_error:
                print(f"API request failed: {str(api_error)}")
                print(f"API response: {getattr(api_error, 'message', str(api_error))}")
                continue
            
            # Process and return the response
            if not text.strip():
                print("Error: Empty response from API")
                continue
                
            try:
                # Try direct JSON parsing first
                print("Attempting direct JSON parse...")
                try:
                    json_data = json.loads(text)
                    if isinstance(json_data, list):
                        print(f"Success! Parsed {len(json_data)} questions directly from JSON")
                        return json.dumps(json_data)
                    print("Warning: Response is JSON but not an array")
                except json.JSONDecodeError as je:
                    print(f"Direct JSON parse failed: {str(je)}")
                
                # Try markdown extraction
                print("Trying markdown code block extraction...")
                match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text)
                if match:
                    try:
                        json_data = json.loads(match.group(1).strip())
                        if isinstance(json_data, list):
                            print(f"Success! Parsed {len(json_data)} questions from markdown code block")
                            return json.dumps(json_data)
                        print("Warning: Extracted content is not a JSON array")
                    except json.JSONDecodeError as je:
                        print(f"Markdown JSON parse failed: {str(je)}")
                
                # Try to find JSON array in the text
                print("Searching for JSON array in text...")
                match = re.search(r'(\[\s*\{.*\}\s*\])', text, re.DOTALL)
                if match:
                    try:
                        json_data = json.loads(match.group(1))
                        if isinstance(json_data, list):
                            print(f"Success! Extracted {len(json_data)} questions from text")
                            return json.dumps(json_data)
                        print("Warning: Extracted content is not a JSON array")
                    except json.JSONDecodeError as je:
                        print(f"JSON array extraction failed: {str(je)}")
                
                # Final fallback - try to clean and parse the entire text
                print("Trying to clean and parse entire text...")
                try:
                    # Clean up common issues
                    cleaned = text.strip()
                    if cleaned.startswith('```'):
                        cleaned = re.sub(r'^```(?:json)?', '', cleaned)
                        cleaned = re.sub(r'```$', '', cleaned).strip()
                    
                    json_data = json.loads(cleaned)
                    if isinstance(json_data, list):
                        print(f"Success! Parsed {len(json_data)} questions after cleaning")
                        return json.dumps(json_data)
                    print("Warning: Cleaned text is not a JSON array")
                except json.JSONDecodeError as je:
                    print(f"Final parse attempt failed: {str(je)}")
                
                print("All parsing attempts failed")
                print("Returning empty array")
                return "[]"
                
            except Exception as e:
                print(f"Unexpected error during response processing: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
                    
        except Exception as e:
            print(f"Error with {strategy['name']} strategy: {str(e)}")
            import traceback
            traceback.print_exc()
            continue
    
    print("\nAll connection strategies failed")
    return "[]"  # Return empty array as string if all strategies fail

# Import re here to ensure it's available
import re
import os
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import requests
from io import BytesIO
import logging

# Load environment variables from .env file
load_dotenv()

# Access environment variables
STABILITY_API_KEY = os.getenv('STABILITY_API_KEY')
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
genai.configure(api_key=GOOGLE_API_KEY)

generation_config = {
  "temperature": 0.8,
  "top_p": 0.9,
  "top_k": 85,
  "max_output_tokens": 300,
  "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
  model_name="gemini-1.5-flash",
  generation_config=generation_config,
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_image_from_text(prompt, img):
    try:
        response = requests.post(
            f"https://api.stability.ai/v2beta/stable-image/generate/ultra",
            headers={
                "authorization": f"Bearer {STABILITY_API_KEY}",
                "accept": "image/*"
            },
            files={"none": ''},
            data={
                "prompt": prompt,
                "mode": "imagetoimage",
                "image": img,
                "output_format": "png"
            },
        )
        
        # Log the request details
        logging.info(f"Request sent to API with prompt: {prompt}")

        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            logging.info("Image generated successfully.")
            return image
        elif response.status_code == 401:
            logging.error("Unauthorized: Check your API key.")
            raise Exception("Unauthorized: Check your API key.")
        elif response.status_code == 400:
            logging.error("Bad Request: Check the request parameters.")
            raise Exception("Bad Request: Check the request parameters.")
        else:
            error_message = response.json().get('message', 'Unknown error')
            logging.error(f"Error {response.status_code}: {error_message}")
            raise Exception(f"Error {response.status_code}: {error_message}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Request failed: {str(e)}")
        raise Exception("Failed to connect to the API. Please check your network connection.")

def get_image_description(image, additional_info, selected_style):
    # Ensure the image is in RGB format
    image = image.convert('RGB')
    
    # Resize the image if it's too large
    max_size = 1024
    if max(image.size) > max_size:
        image.thumbnail((max_size, max_size))

    sketch_prompt = """
Analyze this drawn sketch as a future realistic image. Describe it concisely:
1. Overall scene and setting
2. Main elements and their interactions
3. Implied actions or activities with emotions
4. Mood and atmosphere
5. Symbolic or standout elements
6. Suggested colors and lighting
7. Perspective and point of view
Provide a concise and short description in maximum 10000 characters.
"""
    sketch_prompt += f"The overall main key features are: {additional_info}, this must be in first  " if additional_info else ""

    try:
        response = model.generate_content([image, sketch_prompt])
        return response.text.replace("*", " ").replace("#", " ")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return "Unable to generate description."

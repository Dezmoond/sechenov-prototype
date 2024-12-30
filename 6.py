from PIL import Image
import base64
import io
import ollama

import cv2
import numpy as np
from PIL import Image
def image_to_base64(image_path, width=600):
    # Open the image file
    with Image.open(image_path) as img:
        # Calculate the new height to maintain the aspect ratio
        height = int(img.height * (width / img.width))
        # Resize the image
        img = img.resize((width, height), Image.LANCZOS)

        # Create a BytesIO object to hold the image data
        buffered = io.BytesIO()
        # Save the image to the BytesIO object in PNG format
        img.save(buffered, format="PNG")
        # Get the byte data from the BytesIO object
        img_bytes = buffered.getvalue()
        # Encode the byte data to base64
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64

# Example usage
image_path = 'image/12131314.png' # Replace with your image path
base64_image = image_to_base64(image_path)

# Use Ollama to clean and structure the OCR output
response = ollama.chat(
    model="llama3.2-vision",
    messages=[{
        "role": "user",
        "content": "look on this a sales receipt. The output should be in this format - <Product name> list without numbering. Do not output anything else. Product maybe on Russian language. no English.",
        "images": [base64_image]
    }],
)
# Extract cleaned text
cleaned_text = response['message']['content'].strip()
print(cleaned_text)

#"content": "The image is a book cover. Output should be in this format - <Name of the Book>: <Name of the Author>. Do not output anything else",
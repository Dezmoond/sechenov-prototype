import cv2
import numpy as np
from PIL import Image
import base64
import io
import ollama
import torch
torch.cuda.is_available()
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print('Using device:', device)


def preprocess_image(image_path, preview=False):
    # Load the image with OpenCV
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

    # Resize the image to 800 pixels in width while keeping the aspect ratio
    width = 600
    height = int(img.shape[0] * (width / img.shape[1]))
    img = cv2.resize(img, (width, height), interpolation=cv2.INTER_AREA)

    # Calculate the average brightness of the image
    avg_brightness = np.mean(img)

    # Set alpha and beta based on average brightness
    if avg_brightness < 100:  # Dark image
        alpha = 1.4  # Increase contrast
        beta = 70  # Increase brightness
    elif avg_brightness < 150:  # Medium brightness
        alpha = 1.3
        beta = 60
    else:  # Bright image
        alpha = 1.1  # Lower contrast
        beta = 50  # Slightly decrease brightness

    # Apply contrast and brightness adjustments
    img = cv2.convertScaleAbs(img, alpha=alpha, beta=beta)

    # Apply adaptive thresholding for a more balanced black-and-white effect
    img = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY, 15, 8)

    # Preview the processed image if preview is True
    if preview:
        cv2.imshow("Processed Image", img)
        cv2.waitKey(0)  # Wait until a key is pressed
        cv2.destroyAllWindows()

    # Convert the OpenCV image (grayscale) back to PIL format
    pil_img = Image.fromarray(img)
    return pil_img


def image_to_base64(image, format="JPEG"):  # Изменяем формат на "JPEG"
    # Создаем объект BytesIO для хранения изображения
    buffered = io.BytesIO()
    # Сохраняем изображение в BytesIO объект в указанном формате (JPEG)
    image.save(buffered, format=format)
    # Получаем данные байтов из BytesIO объекта
    img_bytes = buffered.getvalue()
    # Кодируем байтовые данные в base64
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')
    return img_base64

# Preprocess, preview, and convert the image to base64
image_path = 'image/12131314.png'  # Replace with your image path
processed_image = preprocess_image(image_path, preview=True)
base64_image = image_to_base64(processed_image, format="JPEG")

# Use Ollama to clean and structure the OCR output
response = ollama.chat(
    model="llama3.2-vision",
    messages=[{
        "role": "user",
        "content": "This image is a sales receipt. The output should be in this format - <Product name> list without numbering. Do not output anything else. Important Product maybe on Russian language. No English",
        "images": [base64_image]
    }],
)

# Extract cleaned text
cleaned_text = response['message']['content'].strip()
print(cleaned_text)

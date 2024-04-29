import time
from io import BytesIO
import traceback
from imports import client, PILImage, logging, storage_client

style = "Realistic, minimalistic"

def generate_and_save_images(content_type, prompts, gcp_bucket_folder_path):
    saved_images = []

    for index, prompt in enumerate(prompts, start=1):
        card_name = f"{content_type}_{index}"  # e.g., 'word_1', 'idea_1'
        image_params = {
            "model": "dall-e-3",
            "n": 1,
            "size": "1024x1024",
            "prompt": (f"""Please generate a very simple and colorful image illustrating: {prompt}. 
                        Style: {style}"""),
            "user": "myName",
            "response_format": "b64_json"
        }
        try:
            images_response = client.images.generate(**image_params)
            base64_image = images_response.data[0]['b64_json']
            image = PILImage.open(BytesIO(base64.b64decode(base64_image)))
            filename = f"{gcp_bucket_folder_path}/{content_type}_{index}.png"
            image.save(filename)
            logging.info(f"Image saved as {filename}")
            saved_images.append(filename)
            time.sleep(12)  # Throttle rate of image generation if needed
        except Exception as e:
            logging.error(f"An error occurred: {str(e)}")
            traceback.print_exc()

    return saved_images

from imports import client, PILImage
from file_utils import write_file
import base64
from io import BytesIO
import time


def generate_and_save_images(type, prompts, gcp_bucket_folder_path):
    print(prompts)
    print(len(prompts))
    saved_images = []

    for index, prompt in enumerate(prompts, start=1):
        print(index, prompt)
        card_name = f"{type}_{index}"  # Use type to differentiate image files
        image_params = {
            "model": "dall-e-3",
            "n": 1,
            "size": "1024x1024",
            "prompt": (f"""Please generate a very simple and colorful image illustrating: {prompt}. 
                        Style: Realistic, minimalistic"""),
            "user": "myName",
            "response_format": "b64_json"
        }
        try:
            images_response = client.images.generate(**image_params)
            base64_image = images_response.data[0].model_dump()['b64_json']
            image = PILImage.open(BytesIO(base64.b64decode(base64_image)))
            filename = f"{gcp_bucket_folder_path}{card_name}.webp"
            print(filename)

            # Convert image to bytes and save using write_file from file_utils.py
            img_byte_arr = BytesIO()
            image.save(img_byte_arr, format='WebP')
            img_byte_arr.seek(0)  # Move the file pointer to the beginning of the file
            write_file(filename, img_byte_arr, is_binary=True)  # Save to GCP

            print("Image saved as", filename)
            saved_images.append(filename)  # Store the filename for later use
            time.sleep(12)  # Adjust sleep time based on your API rate limit
        except Exception as e:
            print(f"An error occurred: {e}")
    return saved_images

import os
import openai
from main import generate_and_save_images

# Read summaries from file
with open('summaries.txt', 'r') as file:
    summaries_vector = [line.strip() for line in file if line.strip()]


print(type(summaries_vector))
print(len(summaries_vector))
for summary in summaries_vector:
    print(summary)

# Path where images will be saved
image_save_path = "static/images"

# Assuming 'summaries_vector' contains the prompts for image generation
if not os.path.exists(image_save_path):
    os.makedirs(image_save_path)

# Call your function to generate and save images
image_names = generate_and_save_images(summaries_vector, drive_folder_path=image_save_path)

print(f"Generated {len(image_names)} images, saved to {image_save_path}")


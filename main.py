# Imports
import os
import json
import sys
import re
import time
import base64
import requests
from io import BytesIO
from datetime import datetime
from PIL import Image as PILImage
import PyPDF2
import openai
from openai import OpenAI
from datetime import datetime
from flask import Flask, render_template, request, send_from_directory
from flask_socketio import SocketIO
from logging import StreamHandler
from google.cloud import storage
from google.oauth2 import service_account
from itertools import zip_longest

app = Flask(__name__)

socketio = SocketIO(app)
on_heroku = os.environ.get('HEROKU', 'False') == 'True'
bucket_name = 'ainclusive'

def get_gcp_credentials():
    if on_heroku:
        creds_json = os.environ.get("GCP_CREDENTIALS")
        if creds_json:
            creds_dict = json.loads(creds_json)
            return service_account.Credentials.from_service_account_info(creds_dict)
        else:
            raise Exception('GCP credentials not found in environment variable.')
    # If not on Heroku, return None to use default credentials
    return None


def create_storage_client():
    if on_heroku:
        credentials = get_gcp_credentials()
        return storage.Client(credentials=credentials)
    else:
        # Locally, we assume default credentials are set up properly (gcloud auth application-default login)
        return None

# Now, whenever you need a storage client, call create_storage_client():
storage_client = create_storage_client()


# Setting API Key
openai.api_key = os.getenv('OPENAI_API_KEY_TAROT')
client = OpenAI(
    api_key=openai.api_key,
)

def list_gcs_files(bucket_name, prefix):
    storage_client = create_storage_client()
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    return [blob.name for blob in blobs]

# Function to generate GCS URL
def gcs_url(bucket_name, path):
    return f"https://storage.googleapis.com/{bucket_name}/{path}"



# Style for image generation
style = """The style of the image is characterized by its very minimalistic approach, focusing on simplicity and clarity 
to cater to children with learning disabilities. It employs basic shapes to depict 
scenes and characters, ensuring that the elements are easily distinguishable without overwhelming details. 
The realism is toned down to a level where objects and figures are recognizable but rendered in a straightforward, 
non-complex manner. This style avoids intricate patterns, decorations, and text to ensure visual accessibility. 
The background is kept clear and uncluttered, emphasizing the main 
subjects with just enough context to convey the scene. Overall, the style is designed to be visually appealing 
yet simple enough not to distract or confuse young viewers, especially those with learning disabilities.
The target audience is 4 year old toddlers.
The images should be colorful."""


def read_or_fetch(filename, fetch_function, *args, **kwargs):
    dir = '/Users/ula/PycharmProjects/AInclusive/HedgeHog'
    full_path = os.path.join(dir, filename)  # Combine the directory and filename
    if os.path.exists(full_path):
        with open(full_path, 'r') as file:
            return file.read()
    else:
        content = fetch_function(*args, **kwargs)
        with open(full_path, 'w') as file:
            file.write(content)
        return content

def process_pdf(filename):
    with open(filename, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "".join([pdf_reader.pages[page].extract_text() for page in range(len(pdf_reader.pages))])
    return text, len(pdf_reader.pages)

def get_original_text():
    filename = "original_text.txt"
    return read_or_fetch(filename, fetch_major_ideas)

def fetch_major_ideas(text):
    major_ideas_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "system", "content": f"List the major ideas of the {text}."}],
        temperature=0,
        max_tokens=4096,
    )
    major_ideas = major_ideas_response.choices[0].message.content
    return '\n'.join(idea.strip() for idea in major_ideas.split('\n') if idea.strip())

def get_major_ideas(text):
    filename = "major_ideas.txt"
    return read_or_fetch(filename, fetch_major_ideas, text)


def save_summaries_to_file(summaries, filename='summaries.txt'):
    with open(filename, 'w') as file:
        file.write(summaries)

def fetch_summary(major_ideas):
    summaries_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"""Please provide a summary for each major idea in the 
        following list: {major_ideas}. Use simple words that a 4 year old toddler can understand. 
        Each summary should be 2 sentences long."""}],
        temperature=0,
        max_tokens=4096,
    )
    summaries = summaries_response.choices[0].message.content.strip()
    return summaries

def get_summary(major_ideas):
    filename = "text_summary.txt"
    return read_or_fetch(filename, fetch_summary, major_ideas)


def identify_new_words(summaries):
    new_words_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": f"""Here are the summaries: {summaries} 
            For each summary identify 1-2 most challenging words. 
            Example: 
            input (summary): The Inuit built igloos for hunting trips and were patient when catching seals. They knew how to survive in the icy Arctic.
            output (new words): igloos, seals
            You need to only generate the output part. 
            """}
        ],
        temperature=0,
        max_tokens=4096,
    )
    new_words = new_words_response.choices[0].message.content
    print(new_words)
    # remove duplicates
    words = re.findall(r'\b\w+\b', new_words)
    # Create a set from the words to remove duplicates
    unique_words_set = set(words)
    # Optional: Remove any numeric entries that are not part of words if they exist
    unique_words_set = {word for word in unique_words_set if not word.isdigit()}
    # Convert set back to a string of words separated by commas
    unique_words_str = ', '.join(sorted(unique_words_set))
    return unique_words_str

def get_new_words(summary):
    filename = "new_words.txt"
    return read_or_fetch(filename, identify_new_words, summary)

def generate_and_save_images(prompts, drive_folder_path="static/images"):
    print(prompts)
    print(len(prompts))
    saved_images = []
    for index, prompt in enumerate(prompts, start=1):
        card_name = f"SummaryCard_{index}"  # Keep the base name without extension
        file_path = os.path.join(drive_folder_path, f"{card_name}.webp")  # Specify the path with extension

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
            base64_image = images_response.data[0].model_dump()['b64_json']
            image = PILImage.open(BytesIO(base64.b64decode(base64_image)))
            filename = f"{drive_folder_path}/{card_name}.png"  # Correctly sets the path
            print(filename)
            image.save(filename)
            print("so far so good")
            saved_images.append(card_name)  # Store just the filename for later use
            print(f"Image saved as {filename}")
            time.sleep(12)  # Adjust the sleep time as needed based on your rate limit
        except Exception as e:
            import traceback
            print(f"An error occurred: {e}")
            traceback.print_exc()
    return saved_images

def fetch_text_content_from_gcs(bucket_name, file_path):
    storage_client = create_storage_client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.download_as_string().decode('utf-8')

def generate_gcs_url(bucket_name, file_path):
    storage_client = create_storage_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.public_url

@app.route('/hedgehogs.html')
def serve_hedgehog():
    image_files = list_gcs_files(bucket_name, 'hedgehog/images/')
    image_names = [generate_gcs_url(bucket_name, file_path) for file_path in image_files]
    text_content = fetch_text_content_from_gcs(bucket_name, 'hedgehog/original_text.txt')
    major_ideas = fetch_text_content_from_gcs(bucket_name, 'hedgehog/major_ideas.txt')
    major_ideas_content = major_ideas.split('\n')
    new_words = fetch_text_content_from_gcs(bucket_name, 'hedgehog/new_words.txt')
    new_words_content = new_words.split('\n')
    text_summary_content = fetch_text_content_from_gcs(bucket_name, 'hedgehog/text_summary.txt')
    fill_in_game = fetch_text_content_from_gcs(bucket_name, 'hedgehog/fillin.txt')
    not_matching = fetch_text_content_from_gcs(bucket_name, 'hedgehog/not_matching.txt')
    return render_template('hedgehogs.html', image_names=image_names, text=text_content, major_ideas=major_ideas_content,
                           new_words=new_words_content, summaries=text_summary_content,
                           game1_txt=fill_in_game, game2_txt=not_matching)

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    socketio.run(app, debug=True)

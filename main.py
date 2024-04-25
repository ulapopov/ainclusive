# Imports
<<<<<<< HEAD
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
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
from logging import StreamHandler
from google.cloud import storage
from google.oauth2 import service_account
from itertools import zip_longest
from langdetect import detect
=======
from imports import app, socketio, create_storage_client, PILImage, bucket_name, os, json, client
<<<<<<< HEAD
>>>>>>> 8276616 (moved imports to imports.py)
=======
from document_handler import process_pdf
>>>>>>> 9437f4a (moved pdf reading to a separate module)

storage_client = create_storage_client()


def list_gcs_files(bucket_name, prefix):
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
    blob = bucket.blob(file_path)
    return blob.download_as_string().decode('utf-8')


def generate_gcs_url(bucket_name, file_path):
    blob = bucket.blob(file_path)
    return blob.public_url

@app.route('/display/<category>')
def serve_content(category):
    base_path = f'{category}/'
    file_keys = ['original_text', 'major_ideas', 'new_words', 'text_summary', 'fillin', 'not_matching']
    file_paths = {key: f'{base_path}{key}.txt' for key in file_keys}

    # Read content directly from files
    content = {key: read_file(path).split('\n') if key != 'original_text' else read_file(path) for key, path in
               file_paths.items()}

    # Fetch and generate URLs for image files
    image_files = list_gcs_files(bucket_name, f'{base_path}images/')
    image_urls = {file_path: generate_gcs_url(bucket_name, file_path) for file_path in image_files}

    # Organize images by type: words and ideas
    word_image_urls = {i: image_urls.get(f"{base_path}images/words_{i}.jpg", 'No Image Available') for i, word in
                       enumerate(content['new_words'], start=1)}
    idea_image_urls = {i: image_urls.get(f"{base_path}images/ideas_{i}.jpg", 'No Image Available') for i, idea in
                       enumerate(content['major_ideas'], start=1)}

<<<<<<< HEAD
    # Fetch text data
    text_content = fetch_text_content_from_gcs(bucket_name, f'{base_path}original_text.txt')
    major_ideas = fetch_text_content_from_gcs(bucket_name, f'{base_path}major_ideas.txt').split('\n')
    new_words = fetch_text_content_from_gcs(bucket_name, f'{base_path}new_words.txt').split('\n')

    # Detect language of text_content
    language = detect(text_content)
    align_class = 'align-right' if language == 'he' else 'align-left'

    # Create pairs with images, defaulting to 'No Image Available'
    words_and_images = [(word, word_image_dict.get(i + 1, 'No Image Available')) for i, word in enumerate(new_words)]
    ideas_and_images = [(idea, idea_image_dict.get(i + 1, 'No Image Available')) for i, idea in enumerate(major_ideas)]

    return render_template('display.html', words_and_images=words_and_images, text=text_content,
                           ideas_and_images=ideas_and_images, align_class=align_class,
                           summaries=fetch_text_content_from_gcs(bucket_name, f'{base_path}text_summary.txt'),
                           game1_txt=fetch_text_content_from_gcs(bucket_name, f'{base_path}fillin.txt'),
                           game2_txt=fetch_text_content_from_gcs(bucket_name, f'{base_path}not_matching.txt'))
=======
    # Create pairs with images
    words_and_images = [(word, word_image_urls.get(i)) for i, word in enumerate(content['new_words'], start=1)]
    ideas_and_images = [(idea, idea_image_urls.get(i)) for i, idea in enumerate(content['major_ideas'], start=1)]
>>>>>>> 59a1c9d (more elegant serve_content function)

    # Render the template with all gathered data
    return render_template('display.html', words_and_images=words_and_images, text=content['original_text'],
                           ideas_and_images=ideas_and_images, summaries='\n'.join(content['text_summary']),
                           game1_txt='\n'.join(content['fillin']), game2_txt='\n'.join(content['not_matching']))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        # Ensure a file is selected
        if uploaded_file:
            # Strip the .pdf extension to determine the category
            file_category = uploaded_file.filename.replace('.pdf', '')
            # Redirect to the 'serve_content' function with the appropriate category
            return redirect(url_for('serve_content', category=file_category))
        else:
            # Handle the case where no file was selected
            return render_template('index.html', error="Please select a file.")
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)

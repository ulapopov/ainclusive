# Imports
import os
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
from flask import Flask, render_template, request
from flask_socketio import SocketIO
from logging import StreamHandler

app = Flask(__name__)
socketio = SocketIO(app)

# Setting API Key
openai.api_key = os.getenv('OPENAI_API_KEY_TAROT')
client = OpenAI(
    api_key=openai.api_key,
)

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

@app.route('/')
def index():
    text = get_original_text()
    major_ideas = get_major_ideas(text)
    summaries = get_summary(major_ideas)
    new_words = get_new_words(summaries)
    print(new_words)
    image_names = [img for img in os.listdir('static/images/hedgehog') if img.endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    major_ideas_html = major_ideas.replace('\n', '<br>')
    return render_template('index.html', text=text, major_ideas=major_ideas_html,
                           summaries=summaries, new_words=new_words, image_names=image_names)

if __name__ == '__main__':
    socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

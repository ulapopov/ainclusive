import logging
import re
import os
import json
import requests
from datetime import datetime, timedelta
from PIL import Image as PILImage
from PIL import ImageDraw, ImageFont
import openai
from openai import OpenAI
from flask import Flask, render_template, request, send_from_directory, redirect, url_for, session
from flask_socketio import SocketIO
from google.cloud import storage
from google.oauth2 import service_account
from langdetect import detect

# Configure logging at the very beginning
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Logging is configured.")

# App configuration
app = Flask(__name__)
socketio = SocketIO(app)

# Log application start
logging.info("Application configuration started.")

# Other configurations
openai.api_key = os.getenv('OPENAI_API_KEY_TAROT')
client = OpenAI(
    api_key=openai.api_key,
)

bucket_name = 'ula_content'  # Global bucket name used across your application
model = "gpt-4o"


def load_font(font_name, size):
    try:
        return ImageFont.truetype(font_name, size)
    except OSError:
        return ImageFont.load_default()


def get_gcp_credentials():
    """Retrieves GCP credentials from the environment variable."""
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        logging.info("GCP credentials loaded and parsed successfully.")
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        return credentials
    else:
        logging.error('GCP credentials not found in environment variable.')
        raise Exception('GCP credentials not found in environment variable.')


def create_storage_client():
    """Creates a Google Cloud Storage client using the retrieved credentials."""
    logging.info("Attempting to create a storage client...")
    credentials = get_gcp_credentials()
    client = storage.Client(credentials=credentials)
    logging.info("Storage client created successfully.")
    return client


# Initialize storage_client here to capture all log details during the creation
try:
    storage_client = create_storage_client()
except Exception as e:
    logging.error(f"Failed to create storage client: {str(e)}")
    logging.critical("Cannot proceed without a valid storage client. Exiting.")
    raise SystemExit("Failed to create storage client.")


def clean_text(text):
    """Cleans the text by removing numbers, extra spaces, and multiple newlines."""
    if isinstance(text, list):
        cleaned_text = []
        for item in text:
            # Remove numbers and extra spaces
            cleaned_item = re.sub(r'\d+\.\s+', '', item)  # This regex removes numbers followed by dots and spaces
            # Replace multiple newlines with a single newline (optional, based on your needs)
            cleaned_item = re.sub(r'\n+', '\n', cleaned_item)
            cleaned_text.append(cleaned_item)
        return cleaned_text
    else:
        # Remove numbers and extra spaces
        cleaned_text = re.sub(r'\d+\.\s+', '', text)  # This regex removes numbers followed by dots and spaces
        # Replace multiple newlines with a single newline (optional, based on your needs)
        cleaned_text = re.sub(r'\n+', '\n', cleaned_text)
        return cleaned_text


def generate_signed_url(bucket_name, blob_name, expiration=3600):
    """Generates a signed URL for a blob in a Google Cloud Storage bucket."""
    try:
        credentials = get_gcp_credentials()
        storage_client = storage.Client(credentials=credentials)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        return blob.generate_signed_url(expiration=timedelta(seconds=expiration), method='GET')
    except Exception as e:
        logging.error(f"Failed to generate signed URL for {blob_name}: {e}")
        raise


def fetch_text_content_from_gcs(bucket_name, file_path):
    """Fetches text content from a file in a Google Cloud Storage bucket."""
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.download_as_string().decode('utf-8')


def fetch_image_urls(bucket_name, base_path):
    """Fetches signed image URLs from a Google Cloud Storage bucket. Ensures that the path ends correctly with 'images/'."""
    if not base_path.endswith('images/'):
        base_path += 'images/'
    image_files = list_gcs_files(bucket_name, base_path)
    return [generate_signed_url(bucket_name, file_path) for file_path in image_files]


def list_gcs_files(bucket_name, prefix):
    """Lists files in a Google Cloud Storage bucket under a specific prefix."""
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    file_names = [blob.name for blob in blobs]
    logging.info(f"list_gcs_files(): Listing files under prefix {prefix}: {file_names}")
    return file_names


def content_exists(bucket_name, base_path, file_pattern=None):
    """Checks if content exists in a Google Cloud Storage bucket based on the provided base path and file pattern."""
    # Handle the case where file_pattern might be None by defaulting to an empty string
    full_path = f'{base_path}{file_pattern}' if file_pattern else base_path
    image_files = list_gcs_files(bucket_name, full_path)
    exists = len(image_files) > 0
    print(f"Checking content existence in {full_path}: {exists}")
    return exists


def filter_sort_images(image_urls, type_prefix):
    """Filters and sorts image URLs based on the prefix ('words_' or 'ideas_'), followed by a number."""
    filtered_urls = [url for url in image_urls if type_prefix in url.split('/')[-1]]
    sorted_images = {int(url.split('/')[-1].split('_')[1].split('.')[0]): url for url in filtered_urls}
    return sorted_images


def pair_content_with_images(content_list, image_dict):
    """Pairs each content item with its corresponding image, defaulting to 'No Image Available'."""
    return [(content, image_dict.get(i + 1, 'No Image Available')) for i, content in enumerate(content_list)]
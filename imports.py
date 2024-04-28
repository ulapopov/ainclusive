import logging

# Configure logging at the very beginning
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logging.info("Logging is configured.")

import os
import json
from datetime import datetime
from PIL import Image as PILImage
import openai
from openai import OpenAI
from flask import Flask, render_template, request, send_from_directory, redirect, url_for
from flask_socketio import SocketIO
from google.cloud import storage
from google.oauth2 import service_account

# App configuration
app = Flask(__name__)
socketio = SocketIO(app)

# Log application start
logging.info("Application configuration started.")

def get_gcp_credentials():
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        logging.info("GCP credentials loaded and parsed successfully.")
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        logging.info(f"Credentials are: {credentials}")
        return credentials
    else:
        logging.error('GCP credentials not found in environment variable.')
        raise Exception('GCP credentials not found in environment variable.')

def create_storage_client():
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


def list_gcs_files(bucket_name, prefix):
    blobs = storage_client.list_blobs(bucket_name, prefix=prefix)
    return [blob.name for blob in blobs]


def fetch_text_content_from_gcs(bucket_name, file_path):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.download_as_string().decode('utf-8')


def generate_gcs_url(bucket_name, file_path):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file_path)
    return blob.public_url


def fetch_image_urls(bucket_name, base_path):
    """Fetches image URLs from GCS."""
    image_files = list_gcs_files(bucket_name, f'{base_path}images/')
    return [generate_gcs_url(bucket_name, file_path) for file_path in image_files]


def filter_sort_images(image_urls, type_prefix):
    """Filters and sorts image URLs based on the prefix ('words_' or 'ideas_')."""
    filtered_urls = [url for url in image_urls if type_prefix in url]
    return {int(url.split('_')[1].split('.')[0]): url for url in filtered_urls}


def pair_content_with_images(content_list, image_dict):
    """Pairs each content item with its corresponding image, defaulting to 'No Image Available'."""
    return [(content, image_dict.get(i + 1, 'No Image Available')) for i, content in enumerate(content_list)]



# Other configurations
openai.api_key = os.getenv('OPENAI_API_KEY_TAROT')
client = OpenAI(
    api_key=openai.api_key,
)
bucket_name = 'ainclusive'  # Global bucket name used across your application
logging.info("Finished setting up application.")

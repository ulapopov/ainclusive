# imports.py
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

storage_client = storage.Client()
bucket_name = 'ainclusive'  # Global bucket name used across your application

# Setting API Key
openai.api_key = os.getenv('OPENAI_API_KEY_TAROT')
client = OpenAI(
    api_key=openai.api_key,
)

import logging

# Set up basic configuration for logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
    credentials = get_gcp_credentials()
    logging.info(f"Creating storage client with credentials: {credentials}")
    client = storage.Client(credentials=credentials)
    logging.info("Storage client created successfully.")
    return client


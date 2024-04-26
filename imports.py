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

# Configure logging
logging.basicConfig(level=logging.INFO)


def get_gcp_credentials():
    creds_json = os.environ.get("GCP_CREDENTIALS")
    if creds_json:
        creds_dict = json.loads(creds_json)
        logging.info("GCP credentials have been loaded successfully.")
        return service_account.Credentials.from_service_account_info(creds_dict)
    else:
        logging.error('GCP credentials not found in environment variable.')
        raise Exception('GCP credentials not found in environment variable.')


def create_storage_client():
    credentials = get_gcp_credentials()
    return storage.Client(credentials=credentials)


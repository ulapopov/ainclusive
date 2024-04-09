from flask import Flask, jsonify
from io import BytesIO
from PIL import Image, ImageOps, ImageDraw, ImageFilter
import random
import requests
import os
from urllib.parse import quote
from google.cloud import storage
from google.oauth2 import service_account
import json

app = Flask(__name__)

def get_gcp_credentials():
    credentials_json = os.getenv('GCP_CREDENTIALS')
    print(credentials_json)
    if credentials_json:
        credentials_dict = json.loads(credentials_json)
        print(credentials_dict)
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
    else:
        # Assuming GOOGLE_APPLICATION_CREDENTIALS is set for local development
        credentials = None
    return credentials

credentials = get_gcp_credentials()

# Initialize the GCP client
if credentials:
    client = storage.Client(credentials=credentials)
else:
    # Automatically looks for GOOGLE_APPLICATION_CREDENTIALS or falls back to ADC
    client = storage.Client()


@app.route('/')
def home():
    bucket = client.bucket('ainclusive')
    return "Welcome to the bucket"


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))  # Use the PORT environment variable if it's there, otherwise default to 5000
    app.run(debug=True, host='0.0.0.0', port=port)
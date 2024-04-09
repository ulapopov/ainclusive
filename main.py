from flask import Flask, jsonify
import logging
import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import google.auth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

def is_heroku():
    return 'DYNO' in os.environ

def get_gcp_credentials():
    if is_heroku():
        creds_json = os.environ.get("GCP_CREDENTIALS")
        if creds_json is None:
            raise ValueError("GCP_CREDENTIALS not set in Heroku environment.")
        creds_dict = json.loads(creds_json)
        credentials = service_account.Credentials.from_service_account_info(creds_dict)
        project_id = creds_dict.get('project_id')
        return credentials, project_id
    else:
        credentials, project = google.auth.default()
        if not credentials or not project:
            raise ValueError("Could not determine Google credentials. Make sure you have set up the Google Cloud SDK locally.")
        return credentials, project


def list_buckets(credentials, project):
    """Lists all buckets."""
    storage_client = storage.Client(credentials=credentials, project=project)
    buckets = storage_client.list_buckets()
    return [bucket.name for bucket in buckets]

@app.route('/')
def index():
    try:
        credentials, project = get_gcp_credentials()
        buckets = list_buckets(credentials, project)
        return jsonify({"project": project, "buckets": buckets})
    except ValueError as e:
        logger.error(f"Error getting GCP credentials: {str(e)}")
        return jsonify({"error": str(e)}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": "An unexpected error occurred."}), 500

if __name__ == "__main__":
    app.run(debug=True)

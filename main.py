import os
import json
from google.cloud import storage
from google.oauth2 import service_account
import google.auth


def is_heroku():
    return "HEROKU" in os.environ


def get_gcp_credentials():
    creds_json = os.getenv("GCP_CREDENTIALS")
    if creds_json:
        print("GCP_CREDENTIALS from env: True")
        try:
            # Parse the JSON string directly
            creds_info = json.loads(creds_json)
            print("Successfully parsed GCP_CREDENTIALS.")
            credentials = service_account.Credentials.from_service_account_info(creds_info)
            return credentials, creds_info['project_id']
        except json.JSONDecodeError as e:
            print(f"Failed to parse GCP_CREDENTIALS: {e}")
            return None, None
    else:
        print("GCP_CREDENTIALS not set, using default credentials.")
        credentials, project = google.auth.default()
        return credentials, project

def list_buckets():
    """Lists all buckets."""
    credentials, project = get_gcp_credentials()
    print(f"Using project: {project}")
    storage_client = storage.Client(credentials=credentials, project=project)
    try:
        buckets = storage_client.list_buckets()
        print("Buckets:")
        for bucket in buckets:
            print(bucket.name)
    except Exception as e:
        print(f"Error listing buckets: {e}")


from flask import Flask
app = Flask(__name__)

@app.route('/')
def index():
    if is_heroku():
        # Heroku-specific code to use GCP services
        credentials, project = get_gcp_credentials()
        print(f"Using project: {project}")
        buckets_list = list_buckets(credentials, project)
        buckets_str = ', '.join(buckets_list)
        return f"Running on Heroku with GCP. Buckets: {buckets_str}"
    else:
        # Code to run locally without GCP services
        return "Running locally without GCP services."

if __name__ == "__main__":
    app.run(debug=True)

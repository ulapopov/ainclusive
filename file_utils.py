from imports import storage_client, bucket_name

def read_file(file_path):
    """Fetches content from a file in GCS and returns it."""
    # Construct the full path for the GCS bucket
    full_path = f"{bucket_name}/{file_path}"
    blob = storage_client.bucket(bucket_name).blob(file_path)
    if blob.exists():
        return blob.download_as_string().decode('utf-8')
    else:
        print(f"File not found: {full_path}")
        return ""


def write_file(file_path, content):
    """Writes content to a file."""
    with open(file_path, 'w') as file:
        file.write(content)
    return True

from imports import storage_client, bucket_name
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_file(file_path):
    """Fetches content from a file in GCS and returns it. Logs error if file is not found."""
    try:
        blob = storage_client.bucket(bucket_name).blob(file_path)
        if blob.exists():
            return blob.download_as_string().decode('utf-8')
        else:
            logging.warning(f"File not found: {bucket_name}/{file_path}")
            return ""
    except Exception as e:
        logging.error(f"Failed to read file {bucket_name}/{file_path}: {e}")
        return ""


def write_file(file_path, content):
    """Writes content to a file in GCS. Logs the operation status."""
    try:
        blob = storage_client.bucket(bucket_name).blob(file_path)
        blob.upload_from_string(content.encode('utf-8'))
        logging.info(f"File written to: {bucket_name}/{file_path}")
    except Exception as e:
        logging.error(f"Failed to write file {bucket_name}/{file_path}: {e}")


def read_content_files(base_path):
    """Reads content from files and returns them."""
    file_keys = ['original_text', 'major_ideas', 'new_words', 'text_summary', 'fillin', 'not_matching']
    file_paths = {key: f'{base_path}{key}.txt' for key in file_keys}
    content = {}
    for key, path in file_paths.items():
        content[key] = read_file(path).split('\n') if key != 'original_text' else read_file(path)
    return content


def save_summaries_to_file(summaries, filename='summaries.txt'):
    """Writes summaries to a file in GCS and logs the operation status."""
    try:
        full_path = f"summaries/{filename}"  # Adjust the path as necessary
        write_file(full_path, summaries)
        logging.info(f"Summaries saved to: {bucket_name}/{full_path}")
    except Exception as e:
        logging.error(f"Failed to save summaries to {bucket_name}/{full_path}: {e}")

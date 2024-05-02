from imports import storage_client, bucket_name, logging, detect


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_file(file_path):
    """Fetches content from a file in GCS and returns it. Logs error if file is not found."""
    try:
        blob = storage_client.bucket(bucket_name).blob(file_path)
        if blob.exists():
            return blob.download_as_string().decode('utf-8')
        else:
            logging.warning(f"read_file(): File not found: {bucket_name}/{file_path}")
            return ""
    except Exception as e:
        logging.error(f"read_file(): Failed to read file {bucket_name}/{file_path}: {e}")
        return ""


def write_file(file_path, content, is_binary=False):
    try:
        blob = storage_client.bucket(bucket_name).blob(file_path)
        if is_binary:
            blob.upload_from_string(content)  # Content is already binary
        else:
            blob.upload_from_string(content.encode('utf-8'))  # Encode content to bytes
        logging.info(f"write_file(): File written to: {bucket_name}/{file_path}")
    except Exception as e:
        logging.error(f"write_file(): Failed to write file {bucket_name}/{file_path}: {e}")



def read_content_files(base_path):
    """Reads content from files and returns them."""
    logging.basicConfig(level=logging.INFO)
    function_name = "read_content_files"
    file_keys = ['original_text', 'major_ideas', 'new_words', 'text_summary', 'fillin', 'not_matching']
    file_paths = {key: f'{base_path}{key}.txt' for key in file_keys}
    content = {}
    for key, path in file_paths.items():
        try:
            logging.info(f"{function_name}: Reading {path}")
            file_content = read_file(path)
            content[key] = file_content.split('\n') if key != 'original_text' else file_content
            logging.info(f"{function_name}: Successfully read {key}")
        except FileNotFoundError:
            content[key] = [] if key != 'original_text' else ""
            logging.warning(f"{function_name}: File not found: {path}")
        print(f"{function_name}: Processed {key}: {len(content[key])} items")
    return content


def save_summaries_to_file(summaries, filename='summaries.txt'):
    """Writes summaries to a file in GCS and logs the operation status."""
    try:
        full_path = f"summaries/{filename}"  # Adjust the path as necessary
        write_file(full_path, summaries)
        logging.info(f"save_summaries_to_file(): Summaries saved to: {bucket_name}/{full_path}")
    except Exception as e:
        logging.error(f"Failed to save summaries to {bucket_name}/{full_path}: {e}")


def determine_language(text, n=100):  # n defaults to 100, adjust as needed
    try:
        # Log the first n characters of the text to inspect what is being processed
        snippet = text[:n].replace('\n', ' ')  # Replace newlines to keep the log on one line
        logging.info(f"Analyzing text snippet: {snippet}")

        detected_language = detect(text)
        logging.info(f"Detected language: {detected_language}")
        return detected_language
    except Exception as e:
        logging.error(f"Language detection failed: {e}")
        return 'English'  # Fallback to English on detection failure

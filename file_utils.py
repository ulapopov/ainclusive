from imports import storage_client, bucket_name, logging, detect, requests, PILImage
import io
from io import BytesIO


# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def ensure_directory_exists(directory_path):
    try:
        blob = storage_client.bucket(bucket_name).blob(f"{directory_path}/")
        if not blob.exists():
            logging.info(f"Creating directory: {directory_path}")
            blob.upload_from_string('', content_type='application/x-www-form-urlencoded;charset=UTF-8')
        else:
            logging.info(f"Directory already exists: {directory_path}")
    except Exception as e:
        logging.error(f"Failed to ensure directory exists on GCP: {e}")


def read_file(file_path, is_binary=False):
    """Fetches content from a file in GCS and returns it. Logs error if file is not found."""
    try:
        blob = storage_client.bucket(bucket_name).blob(file_path)
        if blob.exists():
            if is_binary:
                return blob.download_as_bytes()  # Use download_as_bytes for binary content
            else:
                return blob.download_as_string().decode('utf-8')
        else:
            logging.warning(f"read_file(): File not found: {bucket_name}/{file_path}")
            return b"" if is_binary else ""
    except Exception as e:
        logging.error(f"read_file(): Failed to read file {bucket_name}/{file_path}: {e}")
        return b"" if is_binary else ""


def save_pdf_to_gcp(image, output_path):
    """Saves a PIL image as a PDF to GCP."""
    output = BytesIO()
    image.save(output, format="PDF")
    pdf_content = output.getvalue()

    if len(pdf_content) > 0:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(output_path)
        blob.upload_from_string(pdf_content, content_type='application/pdf')
        logging.info(f"Successfully saved PDF to {output_path}")
    else:
        logging.error(f"Failed to generate valid PDF content for: {output_path}")


def fetch_image(image_path):
    if image_path.startswith('http'):
        response = requests.get(image_path)
        logging.info(f"Fetched image from URL: {image_path}, Status Code: {response.status_code}, Content Type: {response.headers['Content-Type']}, Content Length: {len(response.content)}")
        if response.status_code == 200 and 'image' in response.headers['Content-Type']:
            try:
                image = PILImage.open(BytesIO(response.content))
                image.verify()  # Verify if it's a valid image
                image = PILImage.open(BytesIO(response.content))  # Reopen since verify() can damage the file object
                logging.info(f"Successfully opened image from URL: {image_path}, Format: {image.format}")
                return image
            except Exception as e:
                logging.error(f"Failed to open image from URL: {image_path}, Error: {e}")
                return None
        else:
            logging.error(f"Failed to fetch a valid image from URL: {image_path}")
            return None
    else:
        image_data = read_file(image_path, is_binary=True)
        logging.info(f"Read image data from path: {image_path}, Data Length: {len(image_data)}")
        try:
            image = PILImage.open(BytesIO(image_data))
            image.verify()  # Verify if it's a valid image
            image = PILImage.open(BytesIO(image_data))  # Reopen since verify() can damage the file object
            logging.info(f"Successfully opened image from path: {image_path}, Format: {image.format}")
            return image
        except Exception as e:
            logging.error(f"Failed to open image from path: {image_path}, Error: {e}")
            return None


def write_file(file_path, content, is_binary=False):
    """Uploads content to a file in GCS."""
    try:
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(file_path)
        if is_binary:
            if isinstance(content, io.BytesIO):
                content = content.getvalue()
            content_type = 'application/octet-stream'
            if file_path.endswith('.png'):
                content_type = 'image/png'
            elif file_path.endswith('.pdf'):
                content_type = 'application/pdf'
            logging.info(f"Writing binary content to: {bucket_name}/{file_path}")
            blob.upload_from_string(content, content_type=content_type)
        else:
            if file_path.endswith('.html'):
                logging.info(f"Writing HTML content to: {bucket_name}/{file_path}")
                blob.upload_from_string(content, content_type='text/html')
            else:
                logging.info(f"Writing text content to: {bucket_name}/{file_path}: {content}")
                if isinstance(content, list):
                    content = '\n'.join(content)  # Convert list to string
                blob.upload_from_string(content, content_type='text/plain')
        logging.info(f"File written to: {bucket_name}/{file_path}")
    except Exception as e:
        logging.error(f"Failed to write file {bucket_name}/{file_path}: {e}")


def read_content_files(base_path):
    """Reads content from files and returns them."""
    logging.basicConfig(level=logging.INFO)
    function_name = "read_content_files"
    file_keys = ['original_text', 'major_ideas', 'new_words', 'words_definitions', 'text_summary',
                 'questions', 'choices', 'statements', 'headers', 'labels']
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


# Define a mapping from language codes to full language names
language_map = {
    'he': 'Hebrew',
    'en': 'English',
    'fr': 'French',
    'es': 'Spanish',
    # Add more mappings as needed
}


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

from imports import os, datetime, app, socketio, client, request, render_template, redirect, url_for, session, bucket_name, logging
from imports import fetch_image_urls, filter_sort_images, pair_content_with_images, content_exists
from file_utils import read_content_files, write_file, read_file, determine_language
from text_generation import generate_text_content
from image_generation import generate_and_save_images
from extract_text import extract_text_and_images

# Ensure session is available
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')

# Global flags for (re)generation
FORCE_REGENERATE_TEXT = True
FORCE_REGENERATE_IMAGES = False
READ_PDF = False  # Set to True if PDF reading and processing is needed

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename.lower().endswith('.pdf'):
            category = uploaded_file.filename[:-4]  # Extract category from filename without the .pdf extension
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            session['timestamp'] = timestamp  # Store the timestamp in the session
            logging.info(f"Timestamp set in session: {timestamp}")

            if READ_PDF:
                logging.info(f"Processing PDF for category {category} at timestamp {timestamp}")
                file_path = f"{category}/{timestamp}/original_text.txt"
                extracted_content = extract_text_and_images(uploaded_file)
                write_file(file_path, extracted_content, is_binary=False)

                # After original_text.txt is ensured in the timestamped directory
                original_text_content = read_file(f"{category}/{timestamp}/original_text.txt")
                language = determine_language(original_text_content)
                session['language'] = language
                logging.info(f"Language set based on {category}/{timestamp}/original_text.txt content: {language}")

                session['text_path'] = f"{category}/{timestamp}/"
                session['image_path'] = f"{category}/{timestamp}/images/"
                logging.info(f"Text path set to: {session['text_path']}, Image path set to: {session['image_path']}")
            else:
                original_text_content = read_file(f"{category}/original_text.txt")
                language = determine_language(original_text_content)
                session['language'] = language
                logging.info(f"Language set based on {category}/original_text.txt content: {language}")

                # Set paths depending on whether to regenerate text or images
                session['text_path'] = f"{category}/default/" if not FORCE_REGENERATE_TEXT else f"{category}/{timestamp}/"
                session['image_path'] = f"{category}/images/" if not FORCE_REGENERATE_IMAGES else f"{category}/{timestamp}/images/"
                logging.info(f"Text path set to: {session['text_path']}, Image path set to: {session['image_path']}")


                # Copy original_text.txt to timestamped directory if text regeneration is forced
                if FORCE_REGENERATE_TEXT:
                    source_path = f"{category}/original_text.txt"
                    destination_path = f"{category}/{timestamp}/original_text.txt"
                    try:
                        # Read the original text content from GCS
                        original_text_content = read_file(source_path)
                        if original_text_content:  # Check if the file was actually read
                            write_file(destination_path, original_text_content, is_binary=False)
                            logging.info(f"Copied original_text.txt from {source_path} to {destination_path}")
                        else:
                            logging.warning(f"No content found to copy from {source_path}")
                    except Exception as e:
                        logging.error(f"Failed to copy original_text.txt from {source_path} to {destination_path}: {e}")

            return redirect(url_for('serve_content', category=category))
        else:
            return render_template('index.html', error="Please select a PDF file.")
    return render_template('index.html')


@app.route('/display/<category>/', methods=['GET'])
def serve_content(category):
    timestamp = session.get('timestamp')
    if not timestamp:
        logging.error("No timestamp found in session.")
        return render_template('error.html', error="Session timestamp error.")
    logging.info(f"Serving content for category {category} with timestamp: {timestamp}")

    # Retrieve the language setting from session and determine text alignment
    language = session.get('language', 'English')  # Default to 'English' if not set
    align_class = 'align-right' if language == 'he' else 'align-left'
    logging.info(f"Determined language from session: {language}")
    logging.info(f"Setting text alignment class: {align_class}")

    # Determine base paths based on regeneration flags
    text_base_path = f'{category}/{timestamp}/' if FORCE_REGENERATE_TEXT else f'{category}/'
    images_base_path = f'{category}/{timestamp}/images/' if FORCE_REGENERATE_IMAGES else f'{category}/images/'

    logging.info(f"Checking content in base path: {text_base_path} and images path: {images_base_path}")

    # Check existence of text and generate if needed
    if FORCE_REGENERATE_TEXT:
        logging.info("Regenerating text content...")
        # Extract text from existing file if needed for generation
        existing_text = read_file(f"{category}/original_text.txt")  # Adjust as necessary to fit your file structure
        generate_text_content(existing_text, category)  # Adjusted to match your function signature

    content = read_content_files(text_base_path)
    if not content:
        logging.error("No content found.")
        return render_template('error.html', error="No content found.")

    # Generate and save images if required
    if FORCE_REGENERATE_IMAGES:
        logging.info("Regenerating images...")
        generate_and_save_images(content['major_ideas'], "ideas", images_base_path)

    image_urls = fetch_image_urls(bucket_name, images_base_path)
    word_image_dict = filter_sort_images(image_urls, 'words_')
    idea_image_dict = filter_sort_images(image_urls, 'ideas_')
    words_and_images = pair_content_with_images(content['new_words'], word_image_dict)
    ideas_and_images = pair_content_with_images(content['major_ideas'], idea_image_dict)

    return render_template('display.html', words_and_images=words_and_images, text=content['original_text'],
                           ideas_and_images=ideas_and_images, summaries='\n'.join(content['text_summary']),
                           game1_txt='\n'.join(content['fillin']), game2_txt='\n'.join(content['not_matching']),
                           align_class=align_class)



if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, debug=True)

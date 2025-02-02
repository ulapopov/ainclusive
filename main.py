from imports import os, datetime, app, socketio, client, request, render_template, redirect, url_for, session, bucket_name, logging
from imports import fetch_image_urls, filter_sort_images, pair_content_with_images, content_exists, generate_signed_url
from file_utils import read_content_files, write_file, read_file, determine_language
from text_generation import generate_text_content
from image_generation import generate_and_save_images
from extract_text import extract_text_and_images
from games import generate_games

# Ensure session is available
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'a_default_secret_key')

# Global flags for (re)generation
FORCE_REGENERATE_TEXT = False
FORCE_REGENERATE_IMAGES = False
FORCE_REGENERATE_GAMES = False
READ_INPUT = False  # Set to True if input reading and processing is needed

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = uploaded_file.filename.lower()
            if filename.endswith('.pdf'):
                category = filename[:-4]  # Extract category from filename without the .pdf extension
            elif filename.endswith('.docx'):
                category = filename[:-5]  # Extract category from filename without the .docx extension
            else:
                return render_template('index.html', error="Please select a PDF or Word file.")

            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
            session['timestamp'] = timestamp  # Store the timestamp in the session
            logging.info(f"Timestamp set in session: {timestamp}")

            if READ_INPUT:
                logging.info(f"Processing file for category {category} at timestamp {timestamp}")
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
                session['game_path'] = f"{category}/{timestamp}/games/"
                logging.info(f"Text path set to: {session['text_path']}, "
                             f"Image path set to: {session['image_path']}, "
                             f"Game path set to: {session['game_path']}")

            else:
                original_text_content = read_file(f"{category}/original_text.txt")
                language = determine_language(original_text_content)
                session['language'] = language
                logging.info(f"Language set based on {category}/original_text.txt content: {language}")

                # Set paths depending on whether to regenerate text or images
                session['text_path'] = f"{category}/default/" if not FORCE_REGENERATE_TEXT else f"{category}/{timestamp}/"
                session['image_path'] = f"{category}/images/" if not FORCE_REGENERATE_IMAGES else f"{category}/{timestamp}/images/"
                session[
                    'game_path'] = f"{category}/games/" if not FORCE_REGENERATE_GAMES else f"{category}/{timestamp}/games/"
                logging.info(
                    f"Text path set to: {session['text_path']}, "
                    f"Image path set to: {session['image_path']}, "
                    f"Game path set to: {session['game_path']}")

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
            return render_template('index.html', error="Please select a file.")
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
    games_base_path = f'{category}/{timestamp}/games/' if FORCE_REGENERATE_GAMES else f'{category}/games/'

    logging.info(
        f"Checking content in base path: {text_base_path}, images path: {images_base_path}, "
        f"and games path: {games_base_path}")

    # Check existence of text and generate if needed
    if FORCE_REGENERATE_TEXT:
        logging.info("Regenerating text content...")
        # Look for original_text.txt in the timestamped folder first
        timestamped_path = f"{category}/{timestamp}/original_text.txt"
        if content_exists(bucket_name, timestamped_path):
            existing_text = read_file(timestamped_path)
        else:
            # If not found in the timestamped folder, look in the category folder
            category_path = f"{category}/original_text.txt"
            if content_exists(bucket_name, category_path):
                existing_text = read_file(category_path)
            else:
                logging.warning("No original_text.txt found in either timestamped or category folder.")
                existing_text = ""
        generate_text_content(existing_text, category)

    content = read_content_files(text_base_path)
    if not content:
        logging.error("No content found.")
        return render_template('error.html', error="No content found.")

    # Generate and save images if required
    if FORCE_REGENERATE_IMAGES:
        logging.info("Regenerating images...")
        generate_and_save_images("ideas", content['major_ideas'], images_base_path)
        generate_and_save_images("words", content['new_words'], images_base_path)

    image_urls = fetch_image_urls(bucket_name, images_base_path)

    word_image_dict = filter_sort_images(image_urls, 'words_')
    idea_image_dict = filter_sort_images(image_urls, 'ideas_')

    words_definitions_images = []

    if 'new_words' in content and 'words_definitions' in content:
        logging.info(f"Found {len(content['new_words'])} new words and {len(content['words_definitions'])} definitions")
        for i, (word, definition) in enumerate(zip(content['new_words'], content['words_definitions'])):
            image = word_image_dict.get(i + 1, 'No Image Available')
            words_definitions_images.append((word, definition, image))
            logging.info(f"Processed word {i + 1}: {word}, definition: {definition}, image: {image}")
    else:
        logging.warning("'new_words' or 'words_definitions' not found in content.")

    logging.info(f"Total words processed: {len(words_definitions_images)}")
    for word, definition, image in words_definitions_images:
        logging.info(f"Word: {word}, Definition: {definition}, Image: {image}")

    ideas_and_images = pair_content_with_images(content['major_ideas'], idea_image_dict)

    # Generate games if required
    if FORCE_REGENERATE_GAMES:
        logging.info("Regenerating games...")
        words_definitions = content.get('words_definitions', [])  # Get the value or use an empty list as default
        generate_games(content['original_text'], content['new_words'], words_definitions, image_urls,
                       content.get('questions', []), content.get('choices', []), content.get('statements', []),
                       content.get('headers', []), content.get('labels', []), games_base_path)

    # Generate URLs for the game files
    matching_game_url = generate_signed_url(bucket_name, f"{games_base_path}matching_game.html")
    fill_in_blank_url = generate_signed_url(bucket_name, f"{games_base_path}fill_in_the_blank.html")
    cut_paste_url = generate_signed_url(bucket_name, f"{games_base_path}cut_and_paste.html")
    table_completion_url = generate_signed_url(bucket_name, f"{games_base_path}table_completion.html")
    coloring_page_url = generate_signed_url(bucket_name, f"{games_base_path}coloring_page.html")
    labeling_activity_url = generate_signed_url(bucket_name, f"{games_base_path}labeling_activity.html")
    sequencing_activity_url = generate_signed_url(bucket_name, f"{games_base_path}sequencing_activity.html")
    short_answer_questions_url = generate_signed_url(bucket_name, f"{games_base_path}short_answer_questions.html")
    true_false_questions_url = generate_signed_url(bucket_name, f"{games_base_path}true_false_questions.html")
    multiple_choice_questions_url = generate_signed_url(bucket_name, f"{games_base_path}multiple_choice_questions.html")

    return render_template('display.html',
                           words_definitions_images=words_definitions_images,
                           text=content['original_text'],
                           ideas_and_images=ideas_and_images,
                           summaries='\n'.join(content['text_summary']),
                           matching_game_url=matching_game_url,
                           fill_in_blank_url=fill_in_blank_url,
                           cut_paste_url=cut_paste_url,
                           table_completion_url=table_completion_url,
                           coloring_page_url=coloring_page_url,
                           labeling_activity_url=labeling_activity_url,
                           sequencing_activity_url=sequencing_activity_url,
                           short_answer_questions_url=short_answer_questions_url,
                           true_false_questions_url=true_false_questions_url,
                           multiple_choice_questions_url=multiple_choice_questions_url,
                           align_class=align_class)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, debug=True)

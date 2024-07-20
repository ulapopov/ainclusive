from warnings import filterwarnings
import datetime
import os
from flask import Flask, render_template, request, redirect, url_for, session
from flask_cors import CORS, cross_origin

from src.imports import logging, generate_signed_url, filter_sort_images, pair_content_with_images, fetch_image_urls
from src.file_utils import read_content_files
from src.methods import (
    read_input, do_not_read_input, force_regenerate_text, force_regenerate_images, force_regenerate_games
)

filterwarnings("ignore")
# App configuration
app = Flask(__name__)
CORS(app)

# Global flags for (re)generation
BUCKET_NAME = os.getenv("BUCKET_NAME")
FORCE_REGENERATE_TEXT = os.getenv("FORCE_REGENERATE_TEXT", 'False').lower() in ('true', '1', 1)
FORCE_REGENERATE_IMAGES = os.getenv("FORCE_REGENERATE_IMAGES", 'False').lower() in ('true', '1', 1)
FORCE_REGENERATE_GAMES = os.getenv("FORCE_REGENERATE_GAMES", 'False').lower() in ('true', '1', 1)
READ_INPUT = os.getenv("READ_INPUT", 'False').lower() in ('true', '1', 1)


@app.route('/', methods=['GET', 'POST'])
@cross_origin()
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file:
            filename = uploaded_file.filename.lower()
            _, file_extension = os.path.splitext(filename)
            if file_extension in ['.pdf', '.docx']:
                category = file_extension[1:]  # Extract category from the file extension
                logging.info(f"Category set to: {category}")
            else:
                return render_template(
                    template_name_or_list='index.html',
                    error="Please select a PDF or Word file."
                )

            timestamp = datetime.datetime.now(datetime.UTC).strftime('%Y%m%d%H%M%S')
            session['timestamp'] = timestamp  # Store the timestamp in the session
            logging.info(f"Timestamp set in session: {timestamp}")

            if READ_INPUT:
                read_input(
                    category=category,
                    timestamp=timestamp,
                    file=uploaded_file,
                    session=session
                )
            else:
                do_not_read_input(
                    category=category,
                    timestamp=timestamp,
                    session=session,
                    conditions=(FORCE_REGENERATE_TEXT, FORCE_REGENERATE_IMAGES, FORCE_REGENERATE_GAMES)
                )
            logging.info(
                f"Text path set to: {session['text_path']}, "
                f"Image path set to: {session['image_path']}, "
                f"Game path set to: {session['game_path']}"
            )
            return redirect(
                location=url_for(
                    endpoint='serve_content',
                    category=category
                )
            )
        else:
            return render_template(template_name_or_list='index.html', error="Please select a file.")
    return render_template(template_name_or_list='index.html')


@app.route('/display/<category>/', methods=['GET'])
@cross_origin()
def serve_content(category):
    timestamp = session.get('timestamp')
    if not timestamp:
        logging.error("No timestamp found in session.")
        return render_template(template_name_or_list='error.html', error="Session timestamp error.")
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
        f"and games path: {games_base_path}"
    )

    # Check existence of text and generate if needed
    force_regenerate_text(category=category, timestamp=timestamp, session=session) if FORCE_REGENERATE_TEXT else None

    content = read_content_files(base_path=text_base_path)
    if not content:
        logging.error("No content found.")
        return render_template(template_name_or_list='error.html', error="No content found.")

    # Generate and save images if required
    force_regenerate_images(content=content, images_base_path=images_base_path) if FORCE_REGENERATE_IMAGES else None

    image_urls = fetch_image_urls(bucket_name=BUCKET_NAME, base_path=images_base_path)

    word_image_dict = filter_sort_images(image_urls=image_urls, type_prefix='words_')
    idea_image_dict = filter_sort_images(image_urls=image_urls, type_prefix='ideas_')

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

    ideas_and_images = pair_content_with_images(
        content_list=content['major_ideas'],
        image_dict=idea_image_dict
    )

    # Generate games if required
    force_regenerate_games(
        content=content,
        image_urls=image_urls,
        games_base_path=games_base_path
    ) if FORCE_REGENERATE_GAMES else None

    return render_template(
        template_name_or_list='display.html',
        words_definitions_images=words_definitions_images,
        text=content['original_text'],
        ideas_and_images=ideas_and_images,
        summaries='\n'.join(content['text_summary']),
        matching_game_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}matching_game.html"
        ),
        fill_in_blank_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}fill_in_the_blank.html"
        ),
        cut_paste_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}cut_and_paste.html"
        ),
        table_completion_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}table_completion.html"
        ),
        coloring_page_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}coloring_page.html"
        ),
        labeling_activity_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}labeling_activity.html"
        ),
        sequencing_activity_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}sequencing_activity.html"
        ),
        short_answer_questions_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}short_answer_questions.html"
        ),
        true_false_questions_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}true_false_questions.html"
        ),
        multiple_choice_questions_url=generate_signed_url(
            bucket_name=BUCKET_NAME,
            blob_name=f"{games_base_path}multiple_choice_questions.html"
        ),
        align_class=align_class
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', debug=True, port=5001)

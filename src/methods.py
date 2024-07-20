from flask.sessions import SessionMixin
import os
from werkzeug.datastructures import FileStorage
from src.extract_text import extract_text_and_images
from src.file_utils import determine_language, write_file, read_file
from src.games import generate_games
from src.image_generation import generate_and_save_images

from src.imports import logging, content_exists
from src.text_generation import generate_text_content

BUCKET_NAME = os.getenv("BUCKET_NAME")


def read_input(
        category: str,
        timestamp: str,
        file: FileStorage,
        session: SessionMixin
):
    logging.info(f"Processing file for category {category} at timestamp {timestamp}")
    file_path = f"{category}/{timestamp}/original_text.txt"
    extracted_content = extract_text_and_images(uploaded_file=file)
    write_file(file_path=file_path, content=extracted_content, is_binary=False)

    # After original_text.txt is ensured in the timestamped directory
    original_text_content = read_file(file_path=f"{category}/{timestamp}/original_text.txt")
    language = determine_language(text=original_text_content)

    session['language'] = language
    session['text_path'] = f"{category}/{timestamp}/"
    session['image_path'] = f"{category}/{timestamp}/images/"
    session['game_path'] = f"{category}/{timestamp}/games/"
    logging.info(f"Language set based on {category}/{timestamp}/original_text.txt content: {language}")


def do_not_read_input(
        category: str,
        timestamp: str,
        session: SessionMixin,
        conditions: tuple
):
    FORCE_REGENERATE_TEXT = conditions[0]
    FORCE_REGENERATE_IMAGES = conditions[1]
    FORCE_REGENERATE_GAMES = conditions[2]

    original_text_content = read_file(file_path=f"{category}/original_text.txt")
    language = determine_language(text=original_text_content)
    session['language'] = language
    # Set paths depending on whether to regenerate text or images
    session['text_path'] = f"{category}/default/" if not FORCE_REGENERATE_TEXT else f"{category}/{timestamp}/"
    session['image_path'] = f"{category}/images/" if not FORCE_REGENERATE_IMAGES else f"{category}/{timestamp}/images/"
    session['game_path'] = f"{category}/games/" if not FORCE_REGENERATE_GAMES else f"{category}/{timestamp}/games/"

    logging.info(f"Language set based on {category}/original_text.txt content: {language}")
    # Copy original_text.txt to timestamped directory if text regeneration is forced
    if FORCE_REGENERATE_TEXT:
        source_path = f"{category}/original_text.txt"
        destination_path = f"{category}/{timestamp}/original_text.txt"
        try:
            # Read the original text content from GCS
            original_text_content = read_file(file_path=source_path)
            if original_text_content:  # Check if the file was actually read
                write_file(file_path=destination_path, content=original_text_content, is_binary=False)
                logging.info(f"Copied original_text.txt from {source_path} to {destination_path}")
            else:
                logging.warning(f"No content found to copy from {source_path}")
        except Exception as e:
            logging.error(f"Failed to copy original_text.txt from {source_path} to {destination_path}: {e}")


def force_regenerate_text(
        category: str,
        timestamp: str,
        session: SessionMixin
):
    logging.info("Regenerating text content...")
    # Look for original_text.txt in the timestamped folder first
    timestamped_path = f"{category}/{timestamp}/original_text.txt"
    if content_exists(bucket_name=BUCKET_NAME, base_path=timestamped_path):
        existing_text = read_file(file_path=timestamped_path)
    else:
        # If not found in the timestamped folder, look in the category folder
        category_path = f"{category}/original_text.txt"
        if content_exists(bucket_name=BUCKET_NAME, base_path=category_path):
            existing_text = read_file(file_path=category_path)
        else:
            logging.warning("No original_text.txt found in either timestamped or category folder.")
            existing_text = ""
    generate_text_content(
        text=existing_text,
        category=category,
        session=session
    )


def force_regenerate_images(
        content: dict,
        images_base_path: str
):
    logging.info("Regenerating images...")
    generate_and_save_images(
        image_type="ideas",
        prompts=content['major_ideas'],
        gcp_bucket_folder_path=images_base_path
    )
    generate_and_save_images(
        image_type="words",
        prompts=content['new_words'],
        gcp_bucket_folder_path=images_base_path
    )


def force_regenerate_games(
        content: dict,
        image_urls: list[str],
        games_base_path: str
):
    logging.info("Regenerating games...")
    words_definitions = content.get('words_definitions', [])  # Get the value or use an empty list as default
    generate_games(
        text=content['original_text'],
        words=content['new_words'],
        definitions=words_definitions,
        images=image_urls,
        questions=content.get('questions', []),
        choices=content.get('choices', []),
        statements=content.get('statements', []),
        headers=content.get('headers', []),
        labels=content.get('labels', []),
        output_path=games_base_path
    )

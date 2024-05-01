from imports import datetime, app, socketio, client, request, render_template, redirect, url_for, bucket_name, logging
from imports import fetch_image_urls, filter_sort_images, pair_content_with_images, content_exists
from file_utils import read_content_files, write_file
from text_generation import generate_text_content
from image_generation import generate_and_save_images
from extract_text import extract_text_and_images


# Global flags for (re)generation
FORCE_REGENERATE_TEXT = False
FORCE_REGENERATE_IMAGES = False
READ_PDF = False # Set to True if PDF reading and processing is needed


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename.lower().endswith('.pdf'):
            category = uploaded_file.filename[:-4]  # Extract category from filename without the .pdf extension

            if READ_PDF:
                # Process the PDF if read_pdf is True
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
                file_path = f"{category}/{timestamp}/original_text.txt"  # Store extracted text here

                # Assume function to process PDF and extract text
                extracted_content = extract_text_and_images(uploaded_file)  # This needs actual implementation
                write_file(file_path, extracted_content, is_binary=False)  # Save the extracted content

                # Redirect to display content with category and timestamp
                return redirect(url_for('serve_content', category=category, timestamp=timestamp))
            else:
                # If read_pdf is False, do not process the file; use existing content
                return redirect(url_for('serve_content', category=category, timestamp="default"))
        else:
            return render_template('index.html', error="Please select a PDF file.")
    return render_template('index.html')


@app.route('/display/<category>/<timestamp>')
def serve_content(category, timestamp):
    timestamped_path = f'{category}/{timestamp}/'
    fallback_path = f'{category}/'

    logging.info(f"Checking content in fallback path: {fallback_path}")
    text_exists = content_exists(bucket_name, fallback_path, 'text_summary.txt')
    images_exist = content_exists(bucket_name, f"{fallback_path}images/", None)
    logging.info(f"Text exists in fallback: {text_exists}, FORCE_REGENERATE_TEXT: {FORCE_REGENERATE_TEXT}")
    logging.info(f"Images exist in fallback: {images_exist}, FORCE_REGENERATE_IMAGES: {FORCE_REGENERATE_IMAGES}")

    base_path = timestamped_path if FORCE_REGENERATE_TEXT or not text_exists else fallback_path

    content = read_content_files(base_path)

    if not content:
        logging.error("No content found.")
        return render_template('error.html', error="No content found.")

    images_base_path = timestamped_path if FORCE_REGENERATE_IMAGES or not images_exist else base_path
    if images_base_path == timestamped_path:
        logging.info("Regenerating images...")
        generate_and_save_images(content['major_ideas'], "ideas", f"{images_base_path}images/")

    image_urls = fetch_image_urls(bucket_name, f"{images_base_path}")
    word_image_dict = filter_sort_images(image_urls, 'words_')
    idea_image_dict = filter_sort_images(image_urls, 'ideas_')
    words_and_images = pair_content_with_images(content['new_words'], word_image_dict)
    ideas_and_images = pair_content_with_images(content['major_ideas'], idea_image_dict)

    return render_template('display.html', words_and_images=words_and_images, text=content['original_text'],
                           ideas_and_images=ideas_and_images, summaries='\n'.join(content['text_summary']),
                           game1_txt='\n'.join(content['fillin']), game2_txt='\n'.join(content['not_matching']))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    socketio.run(app, debug=True)

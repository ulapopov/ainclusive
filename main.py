from imports import app, socketio, client, request, render_template, redirect, url_for, bucket_name
from imports import fetch_image_urls, filter_sort_images, pair_content_with_images
from file_utils import read_content_files, write_file

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files.get('file')
        if uploaded_file and uploaded_file.filename.lower().endswith('.pdf'):
            # Construct the GCS path
            gcs_path = f"pdf_uploads/{uploaded_file.filename}"
            # Read content from uploaded file
            file_content = uploaded_file.read()
            # Call write_file with path and content
            write_file(gcs_path, file_content)
            # Continue with your processing
            return redirect(url_for('serve_content', category=uploaded_file.filename[:-4]))
        else:
            return render_template('index.html', error="Please select a PDF file.")
    return render_template('index.html')

@app.route('/display/<category>')
def serve_content(category):
    base_path = f'{category}/'
    content = read_content_files(base_path)
    image_urls = fetch_image_urls(bucket_name, base_path)
    word_image_dict = filter_sort_images(image_urls, 'words_')
    idea_image_dict = filter_sort_images(image_urls, 'ideas_')
    words_and_images = pair_content_with_images(content['new_words'], word_image_dict)
    ideas_and_images = pair_content_with_images(content['major_ideas'], idea_image_dict)
    return render_template('display.html', words_and_images=words_and_images, text=content['original_text'],
                           ideas_and_images=ideas_and_images, summaries='\n'.join(content['text_summary']),
                           game1_txt='\n'.join(content['fillin']), game2_txt='\n'.join(content['not_matching']))

if __name__ == '__main__':
    socketio.run(app, debug=True)

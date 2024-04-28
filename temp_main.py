from imports import app, socketio, storage_client, PILImage, bucket_name, os, json, client, request, render_template, redirect, url_for
from document_handler import process_pdf
from file_utils import read_file, write_file, read_content_files, save_summaries_to_file, list_gcs_files


# Style for image generation
style = """The style of the image is characterized by its very minimalistic approach, focusing on simplicity and clarity 
to cater to children with learning disabilities. It employs basic shapes to depict 
scenes and characters, ensuring that the elements are easily distinguishable without overwhelming details. 
The realism is toned down to a level where objects and figures are recognizable but rendered in a straightforward, 
non-complex manner. This style avoids intricate patterns, decorations, and text to ensure visual accessibility. 
The background is kept clear and uncluttered, emphasizing the main 
subjects with just enough context to convey the scene. Overall, the style is designed to be visually appealing 
yet simple enough not to distract or confuse young viewers, especially those with learning disabilities.
The target audience is 4 year old toddlers.
The images should be colorful."""


def get_original_text():
    filename = "original_text.txt"
    return read_or_fetch(filename, fetch_major_ideas)


def fetch_major_ideas(text):
    major_ideas_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "system", "content": f"List the major ideas of the {text}."}],
        temperature=0,
        max_tokens=4096,
    )
    major_ideas = major_ideas_response.choices[0].message.content
    return '\n'.join(idea.strip() for idea in major_ideas.split('\n') if idea.strip())


def get_major_ideas(text):
    filename = "major_ideas.txt"
    return read_or_fetch(filename, fetch_major_ideas, text)


def fetch_summary(major_ideas):
    summaries_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"""Please provide a summary for each major idea in the 
        following list: {major_ideas}. Use simple words that a 4 year old toddler can understand. 
        Each summary should be 2 sentences long."""}],
        temperature=0,
        max_tokens=4096,
    )
    summaries = summaries_response.choices[0].message.content.strip()
    return summaries


def get_summary(major_ideas):
    filename = "text_summary.txt"
    return read_or_fetch(filename, fetch_summary, major_ideas)


def identify_new_words(summaries):
    new_words_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": f"""Here are the summaries: {summaries} 
            For each summary identify 1-2 most challenging words. 
            Example: 
            input (summary): The Inuit built igloos for hunting trips and were patient when catching seals. They knew how to survive in the icy Arctic.
            output (new words): igloos, seals
            You need to only generate the output part. 
            """}
        ],
        temperature=0,
        max_tokens=4096,
    )
    new_words = new_words_response.choices[0].message.content
    print(new_words)
    # remove duplicates
    words = re.findall(r'\b\w+\b', new_words)
    # Create a set from the words to remove duplicates
    unique_words_set = set(words)
    # Optional: Remove any numeric entries that are not part of words if they exist
    unique_words_set = {word for word in unique_words_set if not word.isdigit()}
    # Convert set back to a string of words separated by commas
    unique_words_str = ', '.join(sorted(unique_words_set))
    return unique_words_str


def get_new_words(summary):
    filename = "new_words.txt"
    return read_or_fetch(filename, identify_new_words, summary)


def generate_and_save_images(prompts, drive_folder_path="static/images"):
    print(prompts)
    print(len(prompts))
    saved_images = []
    for index, prompt in enumerate(prompts, start=1):
        card_name = f"SummaryCard_{index}"  # Keep the base name without extension
        file_path = os.path.join(drive_folder_path, f"{card_name}.webp")  # Specify the path with extension

        image_params = {
            "model": "dall-e-3",
            "n": 1,
            "size": "1024x1024",
            "prompt": (f"""Please generate a very simple and colorful image illustrating: {prompt}. 
                        Style: {style}"""),
            "user": "myName",
            "response_format": "b64_json"
        }
        try:
            images_response = client.images.generate(**image_params)
            base64_image = images_response.data[0].model_dump()['b64_json']
            image = PILImage.open(BytesIO(base64.b64decode(base64_image)))
            filename = f"{drive_folder_path}/{card_name}.png"  # Correctly sets the path
            print(filename)
            image.save(filename)
            print("so far so good")
            saved_images.append(card_name)  # Store just the filename for later use
            print(f"Image saved as {filename}")
            time.sleep(12)  # Adjust the sleep time as needed based on your rate limit
        except Exception as e:
            import traceback
            print(f"An error occurred: {e}")
            traceback.print_exc()
    return saved_images


@app.route('/display/<category>')
def serve_content(category):
    base_path = f'{category}/'

    # Read content from files
    content = read_content_files(base_path)

    # Fetch and generate URLs for image files
    image_urls = fetch_image_urls(bucket_name, base_path)

    # Filter and sort word and idea images
    word_image_dict = filter_sort_images(image_urls, 'words_')
    idea_image_dict = filter_sort_images(image_urls, 'ideas_')

    # Create pairs with images
    words_and_images = pair_content_with_images(content['new_words'], word_image_dict)
    ideas_and_images = pair_content_with_images(content['major_ideas'], idea_image_dict)

    # Render the template with structured content and image pairs
    return render_template('display.html', words_and_images=words_and_images, text=content['original_text'],
                           ideas_and_images=ideas_and_images, summaries='\n'.join(content['text_summary']),
                           game1_txt='\n'.join(content['fillin']), game2_txt='\n'.join(content['not_matching']))


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        # Ensure a file is selected
        if uploaded_file:
            # Strip the .pdf extension to determine the category
            file_category = uploaded_file.filename.replace('.pdf', '')
            # Redirect to the 'serve_content' function with the appropriate category
            return redirect(url_for('serve_content', category=file_category))
        else:
            # Handle the case where no file was selected
            return render_template('index.html', error="Please select a file.")
    return render_template('index.html')


if __name__ == '__main__':
    socketio.run(app, debug=True)

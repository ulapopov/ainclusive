from imports import logging, load_font, PILImage, ImageDraw, ImageFont, requests
from file_utils import read_file, write_file, ensure_directory_exists, fetch_image, save_pdf_to_gcp
from text_generation import clean_text
from io import BytesIO


def generate_matching_game(words, definitions, output_path):
    logging.info(f"Generating matching game, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Matching Game', font=title_font, fill='black')

    content_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for word, definition in zip(words, definitions):
        draw.text((x_offset, y_offset), word, font=content_font, fill='black')
        draw.text((x_offset + 200, y_offset), definition, font=content_font, fill='black')
        y_offset += 30

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for matching game, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


from jinja2 import Template
from file_utils import write_file


def generate_fill_in_the_blank(text, words, output_path):
    logging.info(f"Generating fill-in-the-blank, output path: {output_path}")

    # Create HTML content using a template
    html_template = """
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; }
            .title { font-size: 24px; font-weight: bold; }
            .content { margin-top: 20px; }
            .word { display: inline-block; margin: 5px; }
        </style>
    </head>
    <body>
        <div class="title">Fill in the Blank</div>
        <div class="content">
            {% for line in text.split('\n') %}
                <p>
                {% for word in line.split() %}
                    {% if word.lower() in words %}
                        <span class="blank">_____</span>
                    {% else %}
                        <span>{{ word }}</span>
                    {% endif %}
                {% endfor %}
                </p>
            {% endfor %}
        </div>
        <div class="content">
            <h3>Word Bank</h3>
            {% for word in words %}
                <span class="word">{{ word }}</span>
            {% endfor %}
        </div>
    </body>
    </html>
    """

    template = Template(html_template)
    html_content = template.render(text=text, words=words)

    # Save the HTML content to a file on GCP
    write_file(output_path, html_content, is_binary=False)

    logging.info(f"Successfully generated HTML for fill-in-the-blank, output path: {output_path}")



def generate_cut_and_paste(images, output_path):
    logging.info(f"Generating cut-and-paste, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Cut and Paste', font=title_font, fill='black')
    x_offset = 50
    y_offset = 100
    for image_path in images:
        image = fetch_image(image_path)
        if not image:
            continue
        worksheet.paste(image, (x_offset, y_offset))
        y_offset += image.height + 20

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for cut-and-paste, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_table_completion(headers, output_path):
    logging.info(f"Generating table completion, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Table Completion', font=title_font, fill='black')

    header_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for header in headers:
        draw.text((x_offset, y_offset), header, font=header_font, fill='black')
        x_offset += 200

    y_offset += 30
    draw.line((50, y_offset, 750, y_offset), fill='black')
    y_offset += 150
    draw.line((50, y_offset, 750, y_offset), fill='black')

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for table completion, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_coloring_page(image_path, output_path):
    logging.info(f"Generating coloring page, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Coloring Page', font=title_font, fill='black')

    image = fetch_image(image_path)
    if not image:
        return

    coloring_image = image.convert('L')
    worksheet.paste(coloring_image, (50, 100))

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for coloring page, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_labeling_activity(image_path, labels, output_path):
    logging.info(f"Generating labeling activity, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Labeling Activity', font=title_font, fill='black')

    labeling_image = fetch_image(image_path)
    if not labeling_image:
        return

    worksheet.paste(labeling_image, (50, 100))

    label_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100 + labeling_image.height + 20
    for label in labels:
        draw.text((x_offset, y_offset), label, font=label_font, fill='black')
        y_offset += 30

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for labeling activity, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_sequencing_activity(images, output_path):
    logging.info(f"Generating sequencing activity, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Sequencing Activity', font=title_font, fill='black')
    x_offset = 50
    y_offset = 100
    for image_path in images:
        image = fetch_image(image_path)
        if not image:
            continue
        worksheet.paste(image, (x_offset, y_offset))
        x_offset += image.width + 20

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for sequencing activity, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_short_answer_questions(questions, output_path):
    logging.info(f"Generating short answer questions, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Short Answer Questions', font=title_font, fill='black')

    question_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for question in questions:
        draw.text((x_offset, y_offset), question, font=question_font, fill='black')
        y_offset += 30

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for short answer questions, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_true_false_questions(statements, output_path):
    logging.info(f"Generating true/false questions, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'True/False Questions', font=title_font, fill='black')

    statement_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for statement in statements:
        draw.text((x_offset, y_offset), statement, font=statement_font, fill='black')
        draw.text((x_offset + 500, y_offset), 'True/False', font=statement_font, fill='black')
        y_offset += 30

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for true/false questions, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


def generate_multiple_choice_questions(questions, choices, output_path):
    logging.info(f"Generating multiple choice questions, output path: {output_path}")
    worksheet = PILImage.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)
    title_font = load_font('arial.ttf', 24)
    draw.text((20, 20), 'Multiple Choice Questions', font=title_font, fill='black')

    question_font = load_font('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for question, choices_list in zip(questions, choices):
        draw.text((x_offset, y_offset), question, font=question_font, fill='black')
        y_offset += 30
        for choice in choices_list:
            draw.text((x_offset + 20, y_offset), choice, font=question_font, fill='black')
            y_offset += 30
        y_offset += 20

    # Save worksheet to GCP
    output = BytesIO()
    worksheet.save(output, format="PDF")
    logging.info(f"Generated PDF for multiple choice questions, length: {output.getbuffer().nbytes}")
    write_file(output_path, output.getvalue(), is_binary=True)


'''
The function takes the following parameters:
text: The simplified text content.
words: The list of words for various activities.
definitions: The list of definitions corresponding to the words.
images: The list of image paths for activities like cut and paste, coloring page, labeling activity, and sequencing activity.
questions: The list of questions for short answer and multiple-choice activities.
choices: The list of choices for multiple-choice questions.
statements: The list of statements for true/false questions.
headers: The list of headers for table completion activity.
labels: The list of labels for labeling activity.
output_path: The output directory path where the generated game worksheets will be saved.
'''
def generate_games(text, words, definitions, images, questions, choices, statements, headers, labels, output_path):
    # Ensure the directory exists
    ensure_directory_exists(output_path)

    # Call the respective game generation functions based on your requirements
    # Pass the necessary data (text, words, definitions, images, questions, choices, statements, headers, labels) to each function
    # Specify the output path for each generated game worksheet

    # Matching Game
    generate_matching_game(words, definitions, f"{output_path}matching_game.pdf")

    # Fill-in-the-Blank
    generate_fill_in_the_blank(text, words, f"{output_path}fill_in_the_blank.html")

    # Cut and Paste
    generate_cut_and_paste(images, f"{output_path}cut_and_paste.pdf")

    # Table Completion
    generate_table_completion(headers, f"{output_path}table_completion.pdf")

    # Coloring Page
    generate_coloring_page(images[0], f"{output_path}coloring_page.pdf")

    # Labeling Activity
    generate_labeling_activity(images[1], labels, f"{output_path}labeling_activity.pdf")

    # Sequencing Activity
    generate_sequencing_activity(images[:5], f"{output_path}sequencing_activity.pdf")

    # Short Answer Questions
    generate_short_answer_questions(questions, f"{output_path}short_answer_questions.pdf")

    # True/False Questions
    generate_true_false_questions(statements, f"{output_path}true_false_questions.pdf")

    # Multiple Choice Questions
    generate_multiple_choice_questions(questions, choices, f"{output_path}multiple_choice_questions.pdf")

    logging.info(f"Games generated and saved to {output_path}")
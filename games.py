from imports import logging
from file_utils import read_file, write_file
from text_generation import clean_text
from PIL import Image, ImageDraw, ImageFont

def generate_matching_game(words, definitions, output_path):
    # Create a new image for the matching game worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Matching Game', font=title_font, fill='black')

    # Write the words and definitions
    content_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for word, definition in zip(words, definitions):
        draw.text((x_offset, y_offset), word, font=content_font, fill='black')
        draw.text((x_offset + 200, y_offset), definition, font=content_font, fill='black')
        y_offset += 30

    # Save the worksheet
    worksheet.save(output_path)

def generate_fill_in_the_blank(text, words, output_path):
    # Create a new image for the fill-in-the-blank worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Fill in the Blank', font=title_font, fill='black')

    # Write the text with blanks
    content_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for line in text.split('\n'):
        for word in line.split():
            if word.lower() in words:
                draw.text((x_offset, y_offset), '___', font=content_font, fill='black')
            else:
                draw.text((x_offset, y_offset), word, font=content_font, fill='black')
            x_offset += 50
        x_offset = 50
        y_offset += 30

    # Write the word choices
    y_offset += 50
    for word in words:
        draw.text((x_offset, y_offset), word, font=content_font, fill='black')
        y_offset += 30

    # Save the worksheet
    worksheet.save(output_path)

def generate_cut_and_paste(images, output_path):
    # Create a new image for the cut-and-paste worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Cut and Paste', font=title_font, fill='black')

    # Paste the images
    x_offset = 50
    y_offset = 100
    for image_path in images:
        image = Image.open(image_path)
        worksheet.paste(image, (x_offset, y_offset))
        y_offset += image.height + 20

    # Save the worksheet
    worksheet.save(output_path)

def generate_table_completion(headers, output_path):
    # Create a new image for the table completion worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Table Completion', font=title_font, fill='black')

    # Write the table headers
    header_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for header in headers:
        draw.text((x_offset, y_offset), header, font=header_font, fill='black')
        x_offset += 200

    # Draw the table lines
    y_offset += 30
    draw.line((50, y_offset, 750, y_offset), fill='black')
    y_offset += 150
    draw.line((50, y_offset, 750, y_offset), fill='black')

    # Save the worksheet
    worksheet.save(output_path)

def generate_coloring_page(image, output_path):
    # Create a new image for the coloring page
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Coloring Page', font=title_font, fill='black')

    # Paste the image
    coloring_image = Image.open(image).convert('L')  # Convert to grayscale
    worksheet.paste(coloring_image, (50, 100))

    # Save the worksheet
    worksheet.save(output_path)

def generate_labeling_activity(image, labels, output_path):
    # Create a new image for the labeling activity worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Labeling Activity', font=title_font, fill='black')

    # Paste the image
    labeling_image = Image.open(image)
    worksheet.paste(labeling_image, (50, 100))

    # Write the labels
    label_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100 + labeling_image.height + 20
    for label in labels:
        draw.text((x_offset, y_offset), label, font=label_font, fill='black')
        y_offset += 30

    # Save the worksheet
    worksheet.save(output_path)

def generate_sequencing_activity(images, output_path):
    # Create a new image for the sequencing activity worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Sequencing Activity', font=title_font, fill='black')

    # Paste the images
    x_offset = 50
    y_offset = 100
    for image_path in images:
        image = Image.open(image_path)
        worksheet.paste(image, (x_offset, y_offset))
        x_offset += image.width + 20

    # Save the worksheet
    worksheet.save(output_path)

def generate_short_answer_questions(questions, output_path):
    # Create a new image for the short answer question worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Short Answer Questions', font=title_font, fill='black')

    # Write the questions
    question_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for question in questions:
        draw.text((x_offset, y_offset), question, font=question_font, fill='black')
        y_offset += 30

    # Save the worksheet
    worksheet.save(output_path)

def generate_true_false_questions(statements, output_path):
    # Create a new image for the true/false question worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'True/False Questions', font=title_font, fill='black')

    # Write the statements
    statement_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for statement in statements:
        draw.text((x_offset, y_offset), statement, font=statement_font, fill='black')
        draw.text((x_offset + 500, y_offset), 'True/False', font=statement_font, fill='black')
        y_offset += 30

    # Save the worksheet
    worksheet.save(output_path)

def generate_multiple_choice_questions(questions, choices, output_path):
    # Create a new image for the multiple-choice question worksheet
    worksheet = Image.new('RGB', (800, 600), color='white')
    draw = ImageDraw.Draw(worksheet)

    # Write the title
    title_font = ImageFont.truetype('arial.ttf', 24)
    draw.text((20, 20), 'Multiple Choice Questions', font=title_font, fill='black')

    # Write the questions and choices
    question_font = ImageFont.truetype('arial.ttf', 16)
    x_offset = 50
    y_offset = 100
    for question, choices_list in zip(questions, choices):
        draw.text((x_offset, y_offset), question, font=question_font, fill='black')
        y_offset += 30
        for choice in choices_list:
            draw.text((x_offset + 20, y_offset), choice, font=question_font, fill='black')
            y_offset += 30
        y_offset += 20

    # Save the worksheet
    worksheet.save(output_path)


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
    # Call the respective game generation functions based on your requirements
    # Pass the necessary data (text, words, definitions, images, questions, choices, statements, headers, labels) to each function
    # Specify the output path for each generated game worksheet

    # Matching Game
    generate_matching_game(words, definitions, f"{output_path}/matching_game.pdf")

    # Fill-in-the-Blank
    generate_fill_in_the_blank(text, words, f"{output_path}/fill_in_the_blank.pdf")

    # Cut and Paste
    generate_cut_and_paste(images, f"{output_path}/cut_and_paste.pdf")

    # Table Completion
    generate_table_completion(headers, f"{output_path}/table_completion.pdf")

    # Coloring Page
    generate_coloring_page(images[0], f"{output_path}/coloring_page.pdf")

    # Labeling Activity
    generate_labeling_activity(images[1], labels, f"{output_path}/labeling_activity.pdf")

    # Sequencing Activity
    generate_sequencing_activity(images[:5], f"{output_path}/sequencing_activity.pdf")

    # Short Answer Questions
    generate_short_answer_questions(questions, f"{output_path}/short_answer_questions.pdf")

    # True/False Questions
    generate_true_false_questions(statements, f"{output_path}/true_false_questions.pdf")

    # Multiple Choice Questions
    generate_multiple_choice_questions(questions, choices, f"{output_path}/multiple_choice_questions.pdf")

    logging.info(f"Games generated and saved to {output_path}")
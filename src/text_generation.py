import os

from src.file_utils import write_file, determine_language, language_map
from src.imports import client, logging, openai, clean_text, fetch_image_urls
import os


def generate_summary(text, language):
    summary_response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "system", "content": f"Please rewrite the following text in {language} using very simple words, "
                                                f"suitable for a 3-4 year old toddler. Use short sentences and common, everyday words that are easy to understand in {language}. "
                                                f"Ensure the grammar is correct and the structure is straightforward. Use the same language as the source ({language}). "
                                                f"Please double-check for any grammatical errors before providing the response. The text: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    summary = summary_response.choices[0].message.content.strip()
    return summary


def identify_main_ideas(text, language):
    attempt_count = 0
    prompt_english = f"Identify 3-4 main ideas in the text posted below. For each main idea, " \
                     f"provide a concise summary that is 1-2 sentences long. Use simple words suitable for a 3-4 year old toddler, " \
                     f"avoiding complex phrases or terminology. The summaries should clearly reflect key points from the text " \
                     f"and be easy to understand. Ensure the grammar is correct. Do not include titles for each idea." \
                     f"Separate each summary with a bullet point." \
                     f"Use the same language as the source (English). " \
                     f"The text: {text}"
    prompt_hebrew = (
        f"זהה 3-4 רעיונות עיקריים בטקסט שלמטה וספק תקציר תמציתי של משפט או שניים לכל רעיון. "
        f"השתמש במילים פשוטות ובהירות, המתאימות לילד בן 3-4, והמנע משימוש בביטויים מורכבים או מונחים טכניים. "
        f"התקצירים צריכים לשקף בבירור את הנקודות המרכזיות מהטקסט ולהיות קלים להבנה. "
        f"חשוב מאוד לשמור על דיוק דקדוקי בכתיבת התגובה. אנא בדוק את הדקדוק בקפידה. "
        f"השתמש בשפה העברית בלבד. הנה דוגמה למבנה התגובה: "
        f"חשוב מאוד לשמור על דיוק דקדוקי בכתיבת התגובה. אנא בדוק את הדקדוק בקפידה. "
        f"השתמש בשפה העברית בלבד. הטקסט: {text}"
    )

    prompt = prompt_hebrew if language == "Hebrew" else prompt_english

    while attempt_count < 3:
        try:
            main_ideas_response = client.chat.completions.create(
                model=os.getenv("MODEL"),
                messages=[{"role": "system", "content": prompt}],
                temperature=0,
                max_tokens=4096,
            )
            main_ideas = main_ideas_response.choices[0].message.content.strip()

            if main_ideas:
                return main_ideas

            # Increment the attempt count and log the retry
            attempt_count += 1
            logging.warning(f"Attempt {attempt_count}: Received an empty response. Retrying...")

        except Exception as e:
            logging.error(f"Failed to identify main ideas on attempt {attempt_count + 1}. Error: {e}")
            attempt_count += 1

    # After 3 failed attempts
    return "Error: Unable to process the request after multiple attempts."



def identify_words_needing_explanation(text, language):
    words_response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "system",
                   "content": f"Identify 5-10 words in the following text that might be too difficult for a toddler to understand. "
                              f"For each word, provide a very simple explanation or synonym in {language}. "
                              f"Use straightforward language suitable for a 3-4 year old. Avoid complex phrases or terminology, and listing the words numerically. "
                              f"Aim for clear and simple explanations, similar to how you would explain things to a young child. "
                              f"For example, if the word is 'thought', explain it as 'thinking about something in your head'. "
                              f"Ensure the grammar is correct. Use the same language as the source ({language}). "
                              f"Here are some examples to guide your explanations: 'Think - when you imagine something in your head', "
                              f"'Heart - the part of your body that beats and keeps you alive'. The text: {text}"}],

        temperature=0,
        max_tokens=4096,
    )
    words_and_definitions = words_response.choices[0].message.content.strip()
    logging.info(f"Received response from the model: {words_and_definitions}")

    # Separate words and definitions
    words = []
    definitions = []
    for line in words_and_definitions.split('\n'):
        parts = line.split(' - ', 1)
        if len(parts) != 2:
            parts = line.split(': ', 1)

        if len(parts) == 2:
            word = parts[0].strip().strip('*')  # Remove asterisks and leading/trailing whitespace
            definition = parts[1].strip()
            words.append(word)
            definitions.append(definition)
        else:
            logging.warning(f"Skipping line due to unexpected format: {line}")

    return words, definitions


def generate_questions(text, language):
    questions_response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "system", "content": f"Generate 5 simple questions based on the following text. The questions should be suitable for a 3-4 year old toddler and test their understanding of the main ideas in the text. Use {language} for the questions. Here is the text: {text}"}],
        temperature=0.7,
        max_tokens=4096,
    )
    questions = questions_response.choices[0].message.content.strip().split("\n")
    return questions

def generate_choices(questions, language):
    choices = []
    for question in questions:
        choices_response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=[{"role": "system", "content": f"Generate 2 plausible answer choices for the following question in {language}. The choices should be suitable for a 3-4 year old toddler. Here is the question: {question}"}],
            temperature=0.7,
            max_tokens=4096,
        )
        choices.append(choices_response.choices[0].message.content.strip().split("\n"))
    return choices

def generate_statements(text, language):
    statements_response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "system", "content": f"Generate 5 simple true or false statements based on the following text. The statements should be suitable for a 3-4 year old toddler and test their understanding of the main ideas in the text. Use {language} for the statements. Here is the text: {text}"}],
        temperature=0.7,
        max_tokens=4096,
    )
    statements = statements_response.choices[0].message.content.strip().split("\n")
    return statements

def generate_headers(main_ideas, language):
    headers_response = client.chat.completions.create(
        model=os.getenv("MODEL"),
        messages=[{"role": "system", "content": f"Generate 3-4 table headers based on the following main ideas from a text. The headers should be suitable for a 3-4 year old toddler and help categorize key information related to the main ideas. Use {language} for the headers. Here are the main ideas: {main_ideas}"}],
        temperature=0.7,
        max_tokens=4096,
    )
    headers = headers_response.choices[0].message.content.strip().split("\n")
    return headers


def generate_labels(images, language):
    labels = []
    for image_url in images:
        labels_response = client.chat.completions.create(
            model=os.getenv("MODEL"),
            messages=[{"role": "system", "content": f"Generate 3-4 simple labels for the image at the following URL: {image_url}. The labels should be suitable for a 3-4 year old toddler and describe key elements or concepts represented in the image. Use {language} for the labels."}],
            temperature=0.7,
            max_tokens=4096,
        )
        labels.append(labels_response.choices[0].message.content.strip().split("\n"))
    return labels

def generate_text_content(text, category, session):
    timestamp = session.get('timestamp')
    if not timestamp:
        logging.error("No timestamp found in session during text generation.")
        raise Exception("Session timestamp is missing.")

    unique_path = f"{category}/{timestamp}/"
    try:
        language_code = determine_language(text)
        language = language_map.get(language_code, 'English')

        summary = generate_summary(text, language)
        major_ideas = identify_main_ideas(summary, language)
        cleaned_major_ideas = clean_text(major_ideas)
        new_words, words_definitions = identify_words_needing_explanation(summary, language)
        logging.info(f"New words generated {new_words}")
        cleaned_new_words = clean_text(new_words)
        logging.info(f"Cleaned new words generated {cleaned_new_words}")
        questions = generate_questions(summary, language)
        choices = generate_choices(questions, language)
        statements = generate_statements(summary, language)
        headers = generate_headers(cleaned_major_ideas, language)

        # Fetch the image URLs using the fetch_image_urls function from imports.py
        image_urls = fetch_image_urls(os.getenv("BUCKET_NAME"), f"{category}/{timestamp}/images/")
        labels = generate_labels(image_urls, language)

    except openai.APIError as e:
        logging.error(f"OpenAI API is currently not accessible. Error: {e}")
        summary = "Summary not available due to API access issue."
        major_ideas = "Main ideas could not be generated."
        new_words = "Terms explanation not accessible."
        words_definitions = []
        questions = []
        choices = []
        statements = []
        headers = []
        labels = []

    # Save generated content in unique path
    write_file(f"{unique_path}text_summary.txt", summary)
    write_file(f"{unique_path}major_ideas.txt", cleaned_major_ideas)
    write_file(f"{unique_path}new_words.txt", cleaned_new_words)
    write_file(f"{unique_path}words_definitions.txt", "\n".join(words_definitions))
    write_file(f"{unique_path}questions.txt", "\n".join(questions))
    write_file(f"{unique_path}choices.txt", "\n".join(["\n".join(choice) for choice in choices]))
    write_file(f"{unique_path}statements.txt", "\n".join(statements))
    write_file(f"{unique_path}headers.txt", "\n".join(headers))
    write_file(f"{unique_path}labels.txt", "\n".join(["\n".join(label) for label in labels]))

    logging.info(f"Text content generated and saved to {unique_path}")
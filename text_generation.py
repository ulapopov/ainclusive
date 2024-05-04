from file_utils import write_file, determine_language, language_map
from image_generation import generate_and_save_images
from imports import client, datetime, session, logging, openai, clean_text


def generate_summary(text, language):
    summary_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
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
                     f"and be easy to understand. Ensure the grammar is correct. Use the same language as the source (English). " \
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
                model="gpt-4-turbo-preview",
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
        model="gpt-4-turbo-preview",
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
    words = words_response.choices[0].message.content.strip()
    return words


def generate_text_content(text, category):
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
        new_words = identify_words_needing_explanation(summary, language)
        cleaned_new_words = clean_text(new_words)
    except openai.APIError as e:  # This captures all client-related issues including bad requests, rate limits, etc.
        logging.error(f"OpenAI API is currently not accessible. Error: {e}")
        summary = "Summary not available due to API access issue."
        main_ideas = "Main ideas could not be generated."
        terms = "Terms explanation not accessible."

    # Save summary, main ideas, and terms in unique path
    write_file(f"{unique_path}text_summary.txt", summary)
    write_file(f"{unique_path}major_ideas.txt", cleaned_major_ideas)
    write_file(f"{unique_path}new_words.txt", cleaned_new_words)

    logging.info(f"Text content generated and saved to {unique_path}")

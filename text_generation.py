from file_utils import write_file, determine_language, language_map
from image_generation import generate_and_save_images
from imports import client, datetime, session, logging


def generate_summary(text):
    language_code = determine_language(text)
    language = language_map.get(language_code, 'English')
    summary_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        # model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Please summarize the following text in {language} using very simple words, "
                                                f"suitable for a 3-4 year old toddler. Use short sentences and common, everyday words that are easy to understand in {language}. "
                                                f"Ensure the grammar is correct and the structure is straightforward. Use the same language as the source ({language}). "
                                                f"Please double-check for any grammatical errors before providing the response. The text: {text}"}],

        temperature=0,
        max_tokens=4096,
    )
    summary = summary_response.choices[0].message.content.strip()
    return summary


def identify_main_ideas(text):
    # Determine the language of the text
    language_code = determine_language(text)
    language = language_map.get(language_code, 'English')
    main_ideas_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        # model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Identify 3-4 main ideas in the text posted below. "
                                                f"For each main idea, provide a concise summary that is 1-2 sentences long. "
                                                f"Use simple words suitable for a 3-4 year old toddler, avoiding complex phrases or terminology. "
                                                f"The summaries should clearly reflect key points from the text and be easy to understand. "
                                                f"Ensure the grammar is correct."
                                                f"Use the same language as the source ({language}). Here’s how you might structure your response: "
                                                f"'1. [Summary of Idea 1] 2. [Summary of Idea 2] 3. [Summary of Idea 3].' The text: {text}"}],

        temperature=0,
        max_tokens=4096,
    )
    main_ideas = main_ideas_response.choices[0].message.content.strip()
    return main_ideas


def identify_words_needing_explanation(text):
    # Determine the language of the text
    language_code = determine_language(text)
    language = language_map.get(language_code, 'English')
    words_response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "system",
                   "content": f"Identify 5-10 words in the following text that might be too difficult for a toddler to understand. "
                              f"For each word, provide a very simple explanation or synonym in {language}. "
                              f"Use straightforward language suitable for a 3-4 year old. Avoid complex phrases or terminology. "
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
    summary = generate_summary(text)
    main_ideas = identify_main_ideas(summary)
    terms = identify_words_needing_explanation(summary)

    # Save summary, main ideas, and terms in unique path
    write_file(f"{unique_path}text_summary.txt", summary)
    write_file(f"{unique_path}major_ideas.txt", main_ideas)
    write_file(f"{unique_path}new_words.txt", terms)

    logging.info(f"Text content generated and saved to {unique_path}")
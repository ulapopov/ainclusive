from file_utils import write_file
from image_generation import generate_and_save_images
from imports import client, datetime, session, logging


def generate_summary(text):
    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Please provide a summary of the following text using simple words that a 3-4 years old toddler can understand."
                                                f"Use the same language as the source."
                                                f"The text: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    summary = summary_response.choices[0].message.content.strip()
    return summary


def identify_main_ideas(text):
    main_ideas_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Identify 3-4 main ideas in the text posted below. List the ideas. "
                                                f"Use simple words that a 3-4 years old toddler can understand. "
                                                f"Each idea should be 1-2 sentences long. "
                                                f"Use the same language as the source."
                                                f"The text: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    main_ideas = main_ideas_response.choices[0].message.content.strip()
    return main_ideas


def identify_words_needing_explanation(text):
    words_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Identify words in the following text that a toddler might not know and explain each using very simple words."
                                                f"Use the same language as the source."
                                                f"The text:  {text}"}],
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
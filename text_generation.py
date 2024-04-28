from file_utils import save_processed_data_to_gcp
from image_generation import generate_images_for_ideas_and_terms
from imports import client


def generate_summary(text):
    summary_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Please provide a summary of the following text using simple words that a 3-4-year-old can understand: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    summary = summary_response.choices[0].message.content.strip()
    return summary


def identify_main_ideas(text):
    main_ideas_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Identify 4 main ideas in the following text. List the ideas using simple words that a 3-4-year-old can understand. Each idea should be 2 sentences long: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    main_ideas = main_ideas_response.choices[0].message.content.strip()
    return main_ideas


def identify_words_needing_explanation(text):
    words_response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "system", "content": f"Identify words in the following text that a toddler might not know and explain each in very simple words: {text}"}],
        temperature=0,
        max_tokens=4096,
    )
    words = words_response.choices[0].message.content.strip()
    return words


def generate_content(text, category):
    summary = generate_summary(text)
    main_ideas = identify_main_ideas(summary)
    terms = identify_words_needing_explanation(summary)
    generate_images_for_ideas_and_terms(main_ideas, terms)
    save_processed_data_to_gcp(summary, main_ideas, terms, category)

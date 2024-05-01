from file_utils import write_file
from image_generation import generate_and_save_images
from imports import client, datetime


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


def generate_text_content(text, category):
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    unique_path = f"{category}/{timestamp}/"
    summary = generate_summary(text)
    main_ideas = identify_main_ideas(summary)
    terms = identify_words_needing_explanation(summary)

    # Save summary, main ideas, and terms in unique path
    write_file(f"{unique_path}summary.txt", summary)
    write_file(f"{unique_path}main_ideas.txt", main_ideas)
    write_file(f"{unique_path}terms.txt", terms)

    # Generate and save images in a subdirectory
    generate_and_save_images(main_ideas, terms, f"{unique_path}images/")

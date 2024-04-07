import fitz  # PyMuPDF

def extract_text_by_paragraph(pdf_path, output_file='extracted_text.txt'):
    doc = fitz.open(pdf_path)
    with open(output_file, 'w') as out:
        for page in doc:
            text = page.get_text("text")
            # Assuming paragraphs are separated by double newlines
            paragraphs = text.split('\n\n')
            for paragraph in paragraphs:
                out.write(paragraph + "\n\n")

    return paragraphs

pdf_path = '/Users/ula/Desktop/AInclusion/input.pdf'
paragraphs = extract_text_by_paragraph(pdf_path)

# Example of iterating over each paragraph
for paragraph in paragraphs:
    # Do something with each paragraph
    print(paragraph)

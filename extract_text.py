import io
import docx
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from docx.document import Document
from imports import logging


def extract_text_and_images(uploaded_file):
    filename = uploaded_file.filename.lower()
    if filename.endswith('.pdf'):
        # Call a function to extract text and images from PDF
        return extract_from_pdf(uploaded_file)
    elif filename.endswith('.docx'):
        # Call a function to extract text and images from Word
        return extract_from_word(uploaded_file)
    else:
        raise ValueError("Unsupported file format")


def extract_from_pdf(pdf_file):
    # Convert the file stream to bytes for processing
    pdf_bytes = pdf_file.read()
    extracted_text = ""

    # Use pdfplumber to extract text directly from bytes
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                extracted_text += f"Page {page_num + 1} text content: {text}\n"
            else:
                extracted_text += f"Page {page_num + 1} does not have text content.\n"

            # Extract images from the page and apply OCR
            images = convert_from_bytes(pdf_bytes, first_page=page_num + 1, last_page=page_num + 1)
            for image_index, image in enumerate(images):
                # OCR the image using pytesseract for Hebrew
                extracted_text += f"Extracted Text from Image {image_index + 1} on Page {page_num + 1}: " + \
                                  pytesseract.image_to_string(image, lang='heb+eng') + "\n"

    return extracted_text


def extract_from_word(word_file):
    doc = docx.Document(word_file)
    extracted_text = ""

    for paragraph in doc.paragraphs:
        extracted_text += paragraph.text + "\n"

    # Extract images from the Word document
    for index, shape in enumerate(doc.inline_shapes):
        try:
            # Check if the shape is a picture
            if shape.type == docx.shape.INLINE_SHAPE.PICTURE:
                # Extract the image data
                image_data = shape._inline.graphic.data

                # Create a BytesIO object from the image data
                image_stream = io.BytesIO(image_data)

                # Open the image using PIL
                img = Image.open(image_stream)

                # OCR the image using pytesseract for Hebrew
                extracted_text += f"Extracted Text from Image {index + 1}: " + \
                    pytesseract.image_to_string(img, lang='heb+eng') + "\n"
        except Exception as e:
            # Handle any exceptions that may occur during image extraction
            logging.error(f"Error extracting image {index + 1}: {e}")

    logging.info(extracted_text)
    return extracted_text
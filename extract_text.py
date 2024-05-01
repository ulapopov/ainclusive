import io
import pdfplumber
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image


def extract_text_and_images(uploaded_file):
    # Convert the file stream to bytes for processing
    pdf_bytes = uploaded_file.read()
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


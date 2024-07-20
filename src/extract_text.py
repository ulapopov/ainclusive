import io
import docx
import pytesseract
from PIL import Image
import fitz
from src.file_utils import read_file, write_file, ensure_directory_exists
from flask import session
import logging


# Set the path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'/usr/local/bin/tesseract'


def convert_page_to_image(page):
    pix = page.get_pixmap()
    img_bytes = pix.tobytes("png")
    return img_bytes


def extract_text_from_image(gcs_path):
    # Read the image file from GCS
    image_bytes = read_file(gcs_path, is_binary=True)
    if not image_bytes:
        logging.error(f"Failed to read image from {gcs_path}")
        return ""

    # Load the image from bytes
    image_pil = Image.open(io.BytesIO(image_bytes))

    # Perform OCR on the image
    ocr_text = pytesseract.image_to_string(image_pil, lang='eng+heb')
    return ocr_text


def extract_from_pdf(pdf_file):
    extracted_text = ""

    # Open the PDF file
    try:
        pdf_doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    except Exception as e:
        logging.error(f"Error opening PDF file: {e}")
        return ""

    timestamp = session.get('timestamp', None)
    if not timestamp:
        logging.error("Timestamp not found in session.")
        return ""

    base_path = f"intermediate_results/{timestamp}/"
    ensure_directory_exists(base_path)

    # Iterate through each page
    for page_num, page in enumerate(pdf_doc):
        try:
            # Extract text content (if available)
            text = page.get_text()
            if text:
                extracted_text += f"Page {page_num + 1} text content: {text}\n"
            else:
                # Convert the entire page to an image (PNG)
                img_bytes = convert_page_to_image(page)

                # Upload the PNG file to GCS
                gcs_path = f"{base_path}page_{page_num + 1}.png"
                write_file(gcs_path, img_bytes, is_binary=True)

                # Call OCR function on the PNG file
                ocr_text = extract_text_from_image(gcs_path)
                if isinstance(ocr_text, str):
                    extracted_text += f"Extracted Text from Page {page_num + 1}: {ocr_text}\n"
                else:
                    logging.warning(f"OCR output is not a string for page {page_num + 1}")

        except Exception as e:
            logging.error(f"Error processing page {page_num + 1}: {e}")
            extracted_text += f"Error processing page {page_num + 1}: {e}\n"

    logging.info("Extracted text length: %d", len(extracted_text))
    return extracted_text


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

    logging.info("Extracted text length: %d", len(extracted_text))
    return extracted_text

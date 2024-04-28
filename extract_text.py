import fitz  # PyMuPDF
from PIL import Image
import pytesseract
import os

def extract_text_and_images(pdf_path):
    # Open the PDF file
    doc = fitz.open(pdf_path)

    # Check for text and image layers in each page
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        if text.strip():
            print(f"Page {page_num + 1} has text content.")
        else:
            print(f"Page {page_num + 1} does not have text content.")

        # Check for images
        if page.get_images(full=True):
            print(f"Page {page_num + 1} contains images.")

    # Extract images from the first page
    image_list = []
    page = doc[0]  # Adjust if multiple pages need processing
    for img_index, img in enumerate(page.get_images(full=True)):
        xref = img[0]
        base_image = doc.extract_image(xref)
        image_bytes = base_image["image"]
        image_ext = base_image["ext"]
        image_path = f"image_Page1_{img_index + 1}.{image_ext}"
        with open(image_path, "wb") as img_file:
            img_file.write(image_bytes)
        image_list.append(image_path)

    doc.close()

    # OCR the images using Tesseract
    for image_file in image_list:
        img = Image.open(image_file)
        text = pytesseract.image_to_string(img, lang='heb')  # Specify Hebrew language with 'lang="heb"'
        print(text)


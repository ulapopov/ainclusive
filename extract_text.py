import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image


def extract_text_and_images(pdf_path):
    # Extract text using pdfplumber for both English and Hebrew
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            text = page.extract_text()
            if text:
                print(f"Page {page_num + 1} has text content: {text}")
            else:
                print(f"Page {page_num + 1} does not have text content.")

            # Extract images from the page and apply OCR
            images = page.images
            for image_index, img_details in enumerate(images):
                # Extract the image
                bbox = (img_details['x0'], img_details['top'], img_details['x1'], img_details['bottom'])
                image = page.to_image(resolution=300)
                cropped_image = image.crop(bbox)
                pil_image = cropped_image.to_image()

                # Save the cropped image
                image_path = f'image_Page{page_num + 1}_{image_index + 1}.png'
                pil_image.save(image_path)

                # OCR the image using pytesseract for Hebrew
                extracted_text = pytesseract.image_to_string(pil_image, lang='heb+eng')
                print(f"Extracted Text from Image {image_index + 1} on Page {page_num + 1}: {extracted_text}")

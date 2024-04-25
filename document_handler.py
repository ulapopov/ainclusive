import PyPDF2

def process_pdf(filename):
    with open(filename, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        text = "".join([pdf_reader.pages[page].extract_text() for page in range(len(pdf_reader.pages))])
    return text, len(pdf_reader.pages)

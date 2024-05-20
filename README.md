# README.md

## Overview
This project provides a comprehensive system for processing textual content from documents (DOCX or PDF), generating summaries, extracting key ideas, and creating visual representations. The workflow involves parsing documents, generating textual content, and creating illustrations for major ideas and new words. The final output is presented through a web interface. The application is built with Flask and deployed on Heroku.

## Workflow Description

### User Interaction:
- **index.html:** Landing page where users upload their input files (DOCX or PDF).
- **display.html:** Webpage where the processed outputs are displayed.

### File Processing and Text Extraction:
- **extract_text.py:** Parses the input file to extract text and save it as `original_text.txt` in a GCS bucket named `ula_content`.

### Text Analysis and Generation:
- **text_generation.py:** Uses the OpenAI model API (GPT-4 Turbo Preview) to generate summaries, major ideas, new words, and games based on the extracted text.

### Image Generation:
- **image_generation.py:** Generates illustrations corresponding to the major ideas and new words using DALL-E 3. These images may also be used in the games.

### File Management:
- **file_utils.py:** Manages all operations related to file handling on Google Cloud Platform (GCP).

### Utilities and Configuration:
- **imports.py:** Manages credentials, imports essential libraries, and handles helper functions.

### Main Application Logic:
- **main.py:** Orchestrates the flow between the web interfaces (index.html and display.html) and the backend processes by receiving parameters from other modules.

## Technical Setup

### Flask Application
The project runs as a Flask application, suitable for managing web requests and serving HTML pages.

### Deployment
The application is deployed on Heroku. Updates to the Heroku deployment are managed through GitHub integration:
- **Command:** `git push heroku main`

### Configuration Files
- **requirements.txt:** Lists all the necessary Python libraries required for the project.
- **Procfile:** Specifies the commands that are executed by the app on startup on Heroku.

### Environment Configuration
- **Project GCP Bucket:** `ula_content`
- **GCP Project Name:** `AInclusive`

### Testing and Development Flags
To test each part separately, use the following flags defined in `main.py`:
- **FORCE_REGENERATE_TEXT:** Set to `False` to prevent re-generation of text unless necessary.
- **FORCE_REGENERATE_IMAGES:** Set to `False` to avoid re-generating images unless needed.
- **READ_INPUT:** Set to `True` to enable reading and processing of the input file.

### Testing
Test the application locally to ensure all parts are functioning correctly before pushing updates to production on Heroku.

## Contact
- **Developer:** Uliana Popov
- **Email:** ula.popov@gmail.com

## No animals and no coders were harmed during writing of this code



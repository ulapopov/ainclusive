import os


def read_file(file_path):
    """Reads content from a file and returns it, ensuring it never returns None."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except FileNotFoundError:
        return ""  # Return an empty string if the file is not found


def write_file(file_path, content):
    """Writes content to a file."""
    with open(file_path, 'w') as file:
        file.write(content)
    return True

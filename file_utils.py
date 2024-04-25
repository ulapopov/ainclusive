import os

def read_file(file_path):
    """Reads content from a file."""
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        return None

def write_file(file_path, content):
    """Writes content to a file."""
    with open(file_path, 'w') as file:
        file.write(content)
    return True

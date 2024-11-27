import os
from uuid import uuid4

UPLOAD_DIR = "files/cv_uploads"
TEMPLATE_DIR = "files/templates"
PDF_DIR = "files/generated_pdfs"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMPLATE_DIR, exist_ok=True)
os.makedirs(PDF_DIR, exist_ok=True)

def generate_unique_filename(original_filename: str) -> str:
    unique_id = uuid4().hex
    return f"{unique_id}_{original_filename}"


def save_cv_file(file):
    filename = generate_unique_filename(file.filename)
    filepath = os.path.join(UPLOAD_DIR, filename)
    file.save(filepath)
    return filepath
import os

class Config:
    # Get absolute paths dynamically based on this file's location
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, "..", ".."))

    # Define specialized directories
    INPUT_PDF_DIR = os.path.join(PROJECT_ROOT, "input_pdfs")
    OUTPUT_PDF_DIR = os.path.join(PROJECT_ROOT, "output_pdfs")

    # App configuration
    SECRET_KEY = os.environ.get("SECRET_KEY", "agentic-reengineering-dev-key")
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB max file size

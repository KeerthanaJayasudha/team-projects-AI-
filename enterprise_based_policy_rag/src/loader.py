import os
from langchain_community.document_loaders import PyPDFLoader
from src.config import DATA_PATH
from src.logger import get_logger

# Create a logger object for this file/module
logger = get_logger(__name__)


def load_documents():

    # Log message → tells that the program is scanning the DATA_PATH folder for PDF files
    logger.info(f"Scanning '{DATA_PATH}' for PDF files...")

    # This list will store all pages from all PDFs
    documents = []

    # Counter to track how many files failed to load
    skipped = 0

    # Loop through every file present inside DATA_PATH directory
    for file in os.listdir(DATA_PATH):

        # Process only files that end with ".pdf"
        if file.endswith(".pdf"):

            # Create full file path (folder path + file name)
            file_path = os.path.join(DATA_PATH, file)

            try:
                # Create PDF loader object for the file
                loader = PyPDFLoader(file_path)

                # Load the PDF → returns list of pages as Document objects
                pages = loader.load()

                # Add all pages into the main documents list
                documents.extend(pages)

                # Log success message with number of pages loaded
                logger.info(f"Loaded: {file} ({len(pages)} pages)")

            except Exception as e:
                # If any error occurs (corrupt PDF / unreadable file)
                skipped += 1

                # Log warning message and skip that file
                logger.warning(f"Skipping '{file}' — could not read: {e}")

    # Final log message showing total pages loaded and skipped files count
    logger.info(f"Load complete. Total pages: {len(documents)} | Skipped files: {skipped}")

    # Return all loaded document pages
    return documents
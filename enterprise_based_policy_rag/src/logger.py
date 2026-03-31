import logging
import os
from datetime import datetime

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

# Log filename includes date so each day gets its own file
log_filename = f"logs/rag_{datetime.now().strftime('%Y-%m-%d')}.log"

# Root logger configuration — set up ONCE here, used everywhere
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)-12s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),  # saves to file
        logging.StreamHandler()                                # also prints to terminal
    ]
)

def get_logger(name: str) -> logging.Logger:
    """
    Call this in every file to get a named logger.
    Usage: logger = get_logger(__name__)
    """
    return logging.getLogger(name)
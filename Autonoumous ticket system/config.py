DATA_PATH = "data/historical_tickets.csv"

FAISS_INDEX_PATH = "embeddings/faiss_index.bin"

TOP_K = 5

OLLAMA_MODEL = "phi3"

CATEGORIES = [
    "Access Issue",
    "Network Issue",
    "Email Service",
    "Database Error",
    "Deployment Issue",
    "Security Issue",
    "Performance Issue",
    "Hardware Issue",
    "Software Bug"
]

# SMTP SETTINGS
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = #Your email
SENDER_PASSWORD = #Your email passkey

ESCALATION_EMAIL = #Your email
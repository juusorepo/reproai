import os
from app.logging_utils import get_logger
from dotenv import load_dotenv
from pathlib import Path

logger = get_logger(__name__)

# Determine the environment (defaults to dev if not set)
ENV = os.getenv("ENV", "dev")

# Load environment variables from .env only if in development mode
if ENV == "dev":
    # Build the absolute path to the .env file in the same folder as config.py
    dotenv_path = Path(__file__).parent / ".env"
    load_dotenv(dotenv_path=dotenv_path, override=True)

# Fetch environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MONGODB_URI = os.getenv("MONGODB_URI")

# Ensure all critical env vars are present
required_vars = [OPENAI_API_KEY, MONGODB_URI]

# If any required vars are missing in production, raise an error
if not all(required_vars):
    if ENV == "prod":
        raise ValueError(
            "Missing required environment variables in production mode. "
            "Please ensure OPENAI_API_KEY and MONGODB_URI are set."
        )
    else:
        print("⚠️ Warning: Some environment variables may be missing in dev mode.")

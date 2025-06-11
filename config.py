import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- Language Model Configuration ---
LLM_API_KEY = os.getenv("LLM_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL")
LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "gpt-4o")

# --- Vision Model Configuration ---
# Often, the vision model uses the same API key and base URL as the language model.
# If they are different, you can set them as separate environment variables.
VISION_API_KEY = os.getenv("VISION_API_KEY", LLM_API_KEY)
VISION_BASE_URL = os.getenv("VISION_BASE_URL", LLM_BASE_URL)
VISION_MODEL_NAME = os.getenv("VISION_MODEL_NAME", "gpt-4-vision-preview")

# --- Project Configuration ---
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
TEMP_DIR = os.getenv("TEMP_DIR", "temp")

# --- Logging Configuration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "logs/paper_agent.log")

import os, sys
from os.path import dirname as up

sys.path.append(os.path.abspath(os.path.join(up(__file__), os.pardir)))

from dotenv import load_dotenv

load_dotenv()

# Define paths
CSV_FILE_PATH = os.getenv("CSV_FILE_PATH")

# Server constants
DB_FILE_PATH = os.getenv("DB_FILE_PATH")

# Client constants
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MCP_CONFIG_FILE_PATH = os.getenv("MCP_CONFIG_FILE_PATH")
MODEL_NAME = os.getenv("MODEL_NAME")
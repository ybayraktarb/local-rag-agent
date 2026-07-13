import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Paths configuration
DOCS_DIR = os.getenv("DOCS_DIR", str(BASE_DIR / "docs"))
DB_DIR = os.getenv("DB_DIR", str(BASE_DIR / "db"))
AUDIT_DIR = os.getenv("AUDIT_DIR", str(BASE_DIR / "audit"))

# Models configuration
CHAT_MODEL = os.getenv("CHAT_MODEL", "qwen2.5:1.5b-instruct")
EMBED_MODEL = os.getenv("EMBED_MODEL", "bge-m3")  # Approved model

# RAG parameters
RETRIEVAL_K = int(os.getenv("RETRIEVAL_K", "3"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.45"))  # Calibrated for bge-m3 real-world queries
CONFIDENCE_HIGH_THRESHOLD = float(os.getenv("CONFIDENCE_HIGH_THRESHOLD", "0.80"))  # UI visual indicator threshold

# Security & Audit Database Key (SQLCipher password)
AUDIT_DB_KEY = os.getenv("AUDIT_DB_KEY", "")

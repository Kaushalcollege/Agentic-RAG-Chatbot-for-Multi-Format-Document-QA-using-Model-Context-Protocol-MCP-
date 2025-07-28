# backend/config.py
import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-70b-8192"

USE_FALLBACK = False
FALLBACK_MODEL = None

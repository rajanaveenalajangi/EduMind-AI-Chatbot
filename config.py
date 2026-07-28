import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Flask app secret key for session signing
    SECRET_KEY = os.environ.get("SECRET_KEY", "edumind_default_secret_key_12345")
    
    # SQLite Database Configuration
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(BASE_DIR, 'edumind.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Gemini API Settings
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

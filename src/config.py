"""
Configuration settings for FloatChat application.
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration."""
    
    # API Keys
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
    
    # Database Configuration
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://localhost:5432/floatchat')
    CHROMA_PERSIST_DIRECTORY = os.getenv('CHROMA_PERSIST_DIRECTORY', './data/chroma_db')
    
    # ARGO Data Configuration
    ARGO_FTP_URL = os.getenv('ARGO_FTP_URL', 'ftp://ftp.ifremer.fr/ifremer/argo')
    INDIAN_ARGO_URL = os.getenv('INDIAN_ARGO_URL', 'https://incois.gov.in/OON/index.jsp')
    
    # Application Settings
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Data Processing
    MAX_PROFILES_PER_FLOAT = 1000
    CHUNK_SIZE = 100
    
    # AI/LLM Settings
    EMBEDDING_MODEL = 'sentence-transformers/all-MiniLM-L6-v2'
    MAX_TOKENS = 4000
    TEMPERATURE = 0.1
    
    @classmethod
    def validate(cls):
        """Validate required configuration."""
        if not cls.GOOGLE_API_KEY:
            raise ValueError("GOOGLE_API_KEY is required")
        return True

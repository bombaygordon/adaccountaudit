import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()

class Config:
    # Flask configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-for-development'
    DEBUG = os.environ.get('DEBUG') or True
    
    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI') or 'sqlite:///app_new.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Remember me cookie duration
    REMEMBER_COOKIE_DURATION = timedelta(days=14)
    
    # API credentials (set these as environment variables in production)
    FB_APP_ID = os.environ.get('FB_APP_ID')
    FB_APP_SECRET = os.environ.get('FB_APP_SECRET')
    
    TIKTOK_APP_ID = os.environ.get('TIKTOK_APP_ID')
    TIKTOK_APP_SECRET = os.environ.get('TIKTOK_APP_SECRET')
    
    # Report settings
    REPORT_STORAGE_PATH = os.environ.get('REPORT_STORAGE_PATH') or 'reports/'
    
    # Security settings
    JWT_SECRET = os.environ.get('JWT_SECRET') or 'your-jwt-secret-for-development'
    JWT_EXPIRATION = int(os.environ.get('JWT_EXPIRATION') or 3600)  # 1 hour
    
    # OpenAI configuration
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    @staticmethod
    def validate():
        """Validate required configuration."""
        if not Config.OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key not found. Please set it using one of these methods:\n"
                "1. Environment variable: OPENAI_API_KEY\n"
                "2. Create a .env file with: OPENAI_API_KEY=your-key-here"
            )
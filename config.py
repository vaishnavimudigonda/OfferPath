import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

# Resolve project root and backend directories
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env file from backend or root directory
env_path_backend = BACKEND_DIR / ".env"
env_path_root = PROJECT_ROOT / ".env"

if env_path_backend.exists():
    load_dotenv(dotenv_path=env_path_backend)
elif env_path_root.exists():
    load_dotenv(dotenv_path=env_path_root)
else:
    load_dotenv()


class Config:
    """Base configuration settings."""
    SECRET_KEY = os.getenv("SECRET_KEY", "offerpath-super-secret-key-change-in-production")
    
    # Database URL configuration (defaults to PostgreSQL, supports SQLite)
    raw_db_url = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/offerpath"
    )
    # Fix legacy postgres:// dialect prefix to modern postgresql://
    if raw_db_url and raw_db_url.startswith("postgres://"):
        raw_db_url = raw_db_url.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_DATABASE_URI = raw_db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload folder: default to OfferPath/uploads
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(PROJECT_ROOT / "uploads"))
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 5 * 1024 * 1024))  # 5MB max
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    
    # Gemini AI API Key
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    
    # JWT Authentication configuration
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", SECRET_KEY)
    JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 72))
    
    # Static folder for frontend
    FRONTEND_DIR = str(PROJECT_ROOT / "frontend")


class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    FLASK_ENV = "development"


class TestingConfig(Config):
    """Testing configuration with shared in-memory SQLite database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool
    }
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    FLASK_ENV = "production"


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig
}

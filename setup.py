"""
Setup script for FloatChat application.
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_requirements():
    """Install required packages."""
    try:
        logger.info("Installing required packages...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        logger.info("Requirements installed successfully!")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing requirements: {e}")
        return False
    return True

def setup_environment():
    """Set up environment variables."""
    env_file = ".env"
    env_example = "env.example"
    
    if not os.path.exists(env_file) and os.path.exists(env_example):
        logger.info("Creating .env file from template...")
        with open(env_example, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        logger.info("Please edit .env file with your API keys and configuration.")
        return True
    elif os.path.exists(env_file):
        logger.info(".env file already exists.")
        return True
    else:
        logger.warning("No environment template found.")
        return False

def create_directories():
    """Create necessary directories."""
    directories = [
        "data",
        "data/chroma_db",
        "data/argo_data",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Created directory: {directory}")

def main():
    """Main setup function."""
    logger.info("Setting up FloatChat...")
    
    # Create directories
    create_directories()
    
    # Install requirements
    if not install_requirements():
        logger.error("Failed to install requirements. Please check your Python environment.")
        return False
    
    # Setup environment
    setup_environment()
    
    logger.info("Setup completed successfully!")
    logger.info("Next steps:")
    logger.info("1. Edit .env file with your Google Gemini API key")
    logger.info("2. Set up PostgreSQL database (optional, SQLite will be used by default)")
    logger.info("3. Run: python scripts/populate_database.py (to add sample data)")
    logger.info("4. Run: streamlit run app.py (to start the application)")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

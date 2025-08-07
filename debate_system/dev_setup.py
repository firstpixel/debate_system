#!/usr/bin/env python3
"""
Development setup script for the debate system.
Installs dependencies and validates the development environment.
"""

import sys
import subprocess
import os
from pathlib import Path

def run_command(cmd, description="", check=True, capture_output=False):
    """Run a command with proper error handling."""
    print(f"📦 {description or cmd}")
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=check)
            return result
        else:
            subprocess.run(cmd, shell=True, check=check)
            return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {e}")
        if capture_output:
            print(f"Output: {e.stdout}")
            print(f"Error: {e.stderr}")
        return None

def install_dependencies():
    """Install Python dependencies."""
    print("🔧 Installing Python dependencies...")
    
    # Try to install from core requirements first
    if os.path.exists("requirements-core.txt"):
        print("Installing core dependencies...")
        run_command("pip install -r requirements-core.txt", "Installing core requirements")
    else:
        print("Core requirements file not found, trying main requirements...")
        if os.path.exists("requirements.txt"):
            run_command("pip install -r requirements.txt", "Installing main requirements")
        else:
            print("No requirements file found, installing essential packages...")
            essential_packages = [
                "streamlit", "ollama", "pymongo", "qdrant-client",
                "numpy", "pandas", "PyYAML", "pydantic", "networkx", "pytest"
            ]
            for package in essential_packages:
                run_command(f"pip install {package}", f"Installing {package}")

def setup_directories():
    """Create necessary directories."""
    print("📁 Setting up directories...")
    
    directories = [
        "sessions",
        "tmp", 
        "logs",
        "output"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created/verified directory: {directory}")

def validate_environment():
    """Validate the development environment."""
    print("🔍 Validating environment...")
    
    # Run the setup validator if it exists
    if os.path.exists("setup_validator.py"):
        print("Running setup validator...")
        run_command("python setup_validator.py", "Environment validation")
    else:
        print("Setup validator not found, running basic checks...")
        
        # Basic Python import checks
        test_imports = [
            "import streamlit",
            "import yaml", 
            "import pytest",
            "import numpy",
            "import pandas"
        ]
        
        for test_import in test_imports:
            try:
                exec(test_import)
                print(f"✅ {test_import}")
            except ImportError as e:
                print(f"❌ {test_import} - {e}")

def create_sample_env():
    """Create a sample .env file if it doesn't exist."""
    if not os.path.exists(".env"):
        print("📝 Creating sample .env file...")
        env_content = """# Debate System Environment Configuration
# Copy this file to .env and modify as needed

# Database URLs (if not using Docker)
# MONGODB_URL=mongodb://localhost:27017
# QDRANT_URL=http://localhost:6333

# LLM Configuration
# OLLAMA_HOST=http://localhost:11434
# DEFAULT_MODEL=gemma3:latest

# Logging
# LOG_LEVEL=INFO

# Session Configuration
# DEFAULT_ROUNDS=3
# DEFAULT_LANGUAGE=english
"""
        with open(".env.sample", "w") as f:
            f.write(env_content)
        print("✅ Created .env.sample file")
    else:
        print("✅ .env file already exists")

def main():
    """Main setup function."""
    print("🚀 Setting up debate system development environment")
    print("=" * 60)
    
    # Check Python version
    python_version = sys.version_info
    if python_version < (3, 8):
        print(f"❌ Python 3.8+ required, found {python_version.major}.{python_version.minor}")
        sys.exit(1)
    print(f"✅ Python {python_version.major}.{python_version.minor} detected")
    
    # Setup steps
    setup_directories()
    install_dependencies()
    create_sample_env()
    validate_environment()
    
    print("\n" + "=" * 60)
    print("🎉 Development environment setup complete!")
    print("\n📋 Next steps:")
    print("1. Start Docker services: docker-compose up -d")
    print("2. Install Ollama: https://ollama.com")
    print("3. Pull a model: ollama pull gemma3:latest")
    print("4. Run the app: python -m streamlit run ui/streamlit_app.py")
    print("\n💡 Run 'python setup_validator.py' to validate your setup")

if __name__ == "__main__":
    main()
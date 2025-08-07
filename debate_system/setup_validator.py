#!/usr/bin/env python3
"""
Setup validation script for the debate system.
Checks dependencies, services, and configuration before running the application.
"""

import sys
import subprocess
import importlib
import os
from typing import List, Tuple, Dict
import yaml

def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is compatible."""
    required_version = (3, 8)
    current_version = sys.version_info[:2]
    
    if current_version >= required_version:
        return True, f"✅ Python {current_version[0]}.{current_version[1]} is compatible"
    else:
        return False, f"❌ Python {required_version[0]}.{required_version[1]}+ required, found {current_version[0]}.{current_version[1]}"

def check_required_packages() -> Tuple[bool, List[str]]:
    """Check if required Python packages are installed."""
    required_packages = [
        'ollama',
        'streamlit', 
        'pymongo',
        'qdrant_client',
        'numpy',
        'pandas',
        'yaml',
        'pydantic',
        'networkx',
        'pytest'
    ]
    
    missing_packages = []
    messages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package.replace('-', '_'))
            messages.append(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            messages.append(f"❌ {package} (missing)")
    
    return len(missing_packages) == 0, messages

def check_ollama_service() -> Tuple[bool, str]:
    """Check if Ollama service is available."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            return True, "✅ Ollama service is running"
        else:
            return False, "❌ Ollama service not responding"
    except FileNotFoundError:
        return False, "❌ Ollama not installed (install from https://ollama.com)"
    except subprocess.TimeoutExpired:
        return False, "❌ Ollama service timeout"
    except Exception as e:
        return False, f"❌ Ollama check failed: {str(e)}"

def check_required_model() -> Tuple[bool, str]:
    """Check if the required model is available."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            models = result.stdout.lower()
            if 'gemma3' in models or 'gemma2' in models:
                return True, "✅ Compatible Gemma model found"
            else:
                return False, "❌ No compatible model found. Run: ollama pull gemma3:latest"
        else:
            return False, "❌ Cannot list Ollama models"
    except Exception as e:
        return False, f"❌ Model check failed: {str(e)}"

def check_config_files() -> Tuple[bool, List[str]]:
    """Check if configuration files are valid."""
    config_dir = "config"
    messages = []
    
    if not os.path.exists(config_dir):
        return False, ["❌ Config directory not found"]
    
    sample_config = os.path.join(config_dir, "config_sample.yaml")
    if os.path.exists(sample_config):
        try:
            with open(sample_config, 'r') as f:
                config = yaml.safe_load(f)
            messages.append("✅ Sample config is valid YAML")
            
            # Check required fields
            required_fields = ['topic', 'personas', 'rounds']
            missing_fields = [field for field in required_fields if field not in config]
            
            if missing_fields:
                messages.append(f"⚠️ Missing fields in sample config: {missing_fields}")
            else:
                messages.append("✅ Sample config has required fields")
                
        except yaml.YAMLError as e:
            messages.append(f"❌ Invalid YAML in sample config: {str(e)}")
        except Exception as e:
            messages.append(f"❌ Config check failed: {str(e)}")
    else:
        messages.append("⚠️ No sample config found")
    
    return True, messages

def check_docker_services() -> Tuple[bool, List[str]]:
    """Check if Docker services are running (optional)."""
    messages = []
    
    try:
        # Check if docker-compose is available
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            messages.append("✅ Docker Compose available")
            
            # Check if services are running
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                if 'mongo' in result.stdout and 'qdrant' in result.stdout:
                    messages.append("✅ MongoDB and Qdrant services detected")
                else:
                    messages.append("⚠️ Start services with: docker-compose up -d")
            else:
                messages.append("⚠️ Run docker-compose up -d to start services")
        else:
            messages.append("⚠️ Docker Compose not available")
            
    except FileNotFoundError:
        messages.append("ℹ️ Docker not available (optional)")
    except Exception as e:
        messages.append(f"⚠️ Docker check failed: {str(e)}")
    
    return True, messages

def main():
    """Run all validation checks."""
    print("🔍 Debate System Setup Validation")
    print("=" * 50)
    
    all_checks_passed = True
    
    # Python version check
    passed, message = check_python_version()
    print(message)
    if not passed:
        all_checks_passed = False
    
    print()
    
    # Package checks
    print("📦 Python Packages:")
    passed, messages = check_required_packages()
    for msg in messages:
        print(f"  {msg}")
    if not passed:
        all_checks_passed = False
        print("  💡 Install with: pip install -r requirements-core.txt")
    
    print()
    
    # Ollama service check
    print("🤖 Ollama Service:")
    passed, message = check_ollama_service()
    print(f"  {message}")
    if not passed:
        all_checks_passed = False
    
    # Model check (only if Ollama is available)
    if passed:
        passed, message = check_required_model()
        print(f"  {message}")
        if not passed:
            all_checks_passed = False
    
    print()
    
    # Config file checks
    print("⚙️ Configuration:")
    passed, messages = check_config_files()
    for msg in messages:
        print(f"  {msg}")
    
    print()
    
    # Docker services check
    print("🐳 Docker Services (Optional):")
    passed, messages = check_docker_services()
    for msg in messages:
        print(f"  {msg}")
    
    print()
    print("=" * 50)
    
    if all_checks_passed:
        print("🎉 All checks passed! The system is ready to run.")
        print("💡 Start with: python -m streamlit run ui/streamlit_app.py")
        return 0
    else:
        print("⚠️ Some issues found. Please fix them before running the system.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
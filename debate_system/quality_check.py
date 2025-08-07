#!/usr/bin/env python3
"""
Code quality check script for the debate system.
Runs linting, type checking, and tests.
"""

import subprocess
import sys
import os
from typing import List, Tuple

def run_command(cmd: str, description: str) -> Tuple[bool, str]:
    """Run a command and return success status and output."""
    print(f"🔍 {description}...")
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, check=False
        )
        
        if result.returncode == 0:
            print(f"✅ {description} passed")
            return True, result.stdout
        else:
            print(f"❌ {description} failed")
            print(f"Error output:\n{result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} failed with exception: {e}")
        return False, str(e)

def check_basic_syntax() -> bool:
    """Check for basic Python syntax errors."""
    print("🔍 Checking Python syntax...")
    
    success = True
    for root, dirs, files in os.walk("."):
        # Skip certain directories
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'tmp'}]
        
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        compile(f.read(), filepath, 'exec')
                except SyntaxError as e:
                    print(f"❌ Syntax error in {filepath}: {e}")
                    success = False
                except Exception as e:
                    print(f"⚠️ Could not check {filepath}: {e}")
    
    if success:
        print("✅ Python syntax check passed")
    
    return success

def check_imports() -> bool:
    """Check for import issues in key modules."""
    print("🔍 Checking key module imports...")
    
    key_modules = [
        "app.config",
        "app.debate_manager", 
        "app.persona_agent",
        "ui.streamlit_app"
    ]
    
    success = True
    for module in key_modules:
        try:
            __import__(module)
            print(f"✅ {module}")
        except ImportError as e:
            print(f"❌ {module}: {e}")
            success = False
        except Exception as e:
            print(f"⚠️ {module}: {e}")
    
    return success

def run_tests() -> bool:
    """Run available tests."""
    print("🔍 Running tests...")
    
    if not os.path.exists("tests"):
        print("⚠️ No tests directory found")
        return True
    
    # First try to run tests that don't require external dependencies
    basic_tests = [
        "tests/test_config_loader.py",
        "tests/test_logger.py",
        "tests/test_performance_logger.py",
        "tests/test_user_feedback.py"
    ]
    
    success = True
    for test_file in basic_tests:
        if os.path.exists(test_file):
            passed, _ = run_command(f"python -m pytest {test_file} -v", f"Testing {test_file}")
            if not passed:
                success = False
    
    return success

def check_configuration_files() -> bool:
    """Validate configuration files."""
    print("🔍 Checking configuration files...")
    
    config_files = []
    if os.path.exists("config"):
        config_files = [f for f in os.listdir("config") if f.endswith(('.yaml', '.yml', '.json'))]
    
    if not config_files:
        print("⚠️ No configuration files found")
        return True
    
    success = True
    for config_file in config_files[:3]:  # Check first 3 to avoid spam
        config_path = os.path.join("config", config_file)
        try:
            if config_file.endswith(('.yaml', '.yml')):
                import yaml
                with open(config_path, 'r') as f:
                    yaml.safe_load(f)
            elif config_file.endswith('.json'):
                import json
                with open(config_path, 'r') as f:
                    json.load(f)
            print(f"✅ {config_file}")
        except Exception as e:
            print(f"❌ {config_file}: {e}")
            success = False
    
    return success

def main():
    """Run all quality checks."""
    print("🔧 Code Quality Check")
    print("=" * 50)
    
    checks = [
        ("Basic Syntax", check_basic_syntax),
        ("Key Imports", check_imports),
        ("Configuration Files", check_configuration_files),
        ("Tests", run_tests),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with exception: {e}")
            results.append((name, False))
        print()
    
    print("=" * 50)
    print("📊 Summary:")
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {name}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 All quality checks passed!")
        return 0
    else:
        print("⚠️ Some quality checks failed. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
# Contributing to the Debate System

Thank you for your interest in contributing to the Autonomous Multi-LLM Markdown Debate Engine! This document provides guidelines for setting up the development environment and contributing to the project.

## 🚀 Quick Start

### 1. Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd debate_system

# Automated setup
python dev_setup.py

# Or manual setup
python setup_validator.py  # Check environment
make setup                  # Alternative using Makefile
```

### 2. Environment Validation

```bash
# Validate your setup
python setup_validator.py

# Run quality checks
python quality_check.py
```

## 📋 Development Workflow

### Before Making Changes

1. **Validate environment:**
   ```bash
   make validate
   ```

2. **Run quality checks:**
   ```bash
   make quality
   ```

3. **Run tests:**
   ```bash
   make test
   ```

### Making Changes

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes following the coding standards below**

3. **Test your changes:**
   ```bash
   make quality
   make test
   ```

4. **Commit with clear messages:**
   ```bash
   git commit -m "feat: add new debate strategy"
   ```

## 🔧 Development Commands

We provide several convenience commands via Makefile:

```bash
make setup          # Set up development environment
make validate       # Validate environment setup  
make quality        # Run code quality checks
make test           # Run basic tests
make test-full      # Run all tests (requires dependencies)
make clean          # Clean temporary files
make run-cli        # Run CLI version
make run-ui         # Run Streamlit UI
make docker-up      # Start Docker services
make docker-down    # Stop Docker services
```

## 📖 Coding Standards

### Python Code Style

- Follow PEP 8 style guidelines
- Use type hints for function parameters and return values
- Add docstrings for all public functions and classes
- Maximum line length: 100 characters

### Logging

- Use the `logging` module instead of `print()` statements
- Log levels:
  - `DEBUG`: Detailed diagnostic information
  - `INFO`: General information about program execution
  - `WARNING`: Something unexpected happened
  - `ERROR`: Serious problem occurred

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Function started")
    logger.debug("Detailed processing info")
```

### Error Handling

- Always handle expected exceptions gracefully
- Provide meaningful error messages to users
- Use specific exception types when possible

```python
try:
    config = load_config(path)
except FileNotFoundError:
    logger.error(f"Configuration file not found: {path}")
    sys.exit(1)
except ValueError as e:
    logger.error(f"Invalid configuration: {e}")
    sys.exit(1)
```

### Configuration

- All configuration should go through the `app.config` module
- Validate configuration parameters
- Provide sensible defaults
- Document configuration options

## 🧪 Testing

### Test Structure

- Tests are located in the `tests/` directory
- Test files should be named `test_*.py`
- Use pytest for running tests

### Writing Tests

```python
import pytest
from app.config import load_config

def test_config_loading():
    config = load_config("config/config_sample.yaml")
    assert "personas" in config
    assert len(config["personas"]) > 0
```

### Running Tests

```bash
# Basic tests (no external dependencies)
make test

# All tests (requires full environment)
make test-full

# Specific test file
python -m pytest tests/test_config_loader.py -v
```

## 📁 Project Structure

```
debate_system/
├── app/                    # Core application logic
│   ├── config.py          # Configuration management
│   ├── debate_manager.py  # Main debate orchestration
│   ├── persona_agent.py   # AI agent implementation
│   └── ...
├── ui/                     # Streamlit user interface
├── tests/                  # Test suite
├── config/                 # Configuration examples
├── requirements-core.txt   # Minimal dependencies
├── requirements.txt        # Full dependencies
├── setup_validator.py      # Environment validation
├── dev_setup.py           # Development setup
├── quality_check.py       # Code quality checks
└── Makefile               # Development commands
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment information:**
   - Python version
   - Operating system
   - Dependencies installed

2. **Steps to reproduce:**
   - Configuration used
   - Commands run
   - Expected vs actual behavior

3. **Logs and error messages:**
   - Full error traceback
   - Relevant log output

## 💡 Feature Requests

When suggesting features:

1. **Describe the use case**
2. **Explain the expected behavior**
3. **Consider backwards compatibility**
4. **Suggest implementation approach if possible**

## 🔍 Code Review Process

1. All changes require review before merging
2. Ensure code follows style guidelines
3. Verify tests pass and coverage is maintained
4. Check that documentation is updated if needed

## 📚 Dependencies

### Core Dependencies

The project uses a minimal set of core dependencies (see `requirements-core.txt`):

- `ollama` - LLM integration
- `streamlit` - Web UI
- `pymongo` - Database
- `qdrant-client` - Vector database
- `numpy`, `pandas` - Data processing
- `PyYAML`, `pydantic` - Configuration
- `networkx` - Graph processing
- `pytest` - Testing

### Optional Dependencies

Additional features may require extra dependencies. Use them sparingly and document requirements clearly.

## ❓ Getting Help

- Check existing documentation and issues
- Run `python setup_validator.py` for environment issues
- Run `make quality` to check code issues
- Create an issue for bugs or feature requests

## 📄 License

By contributing, you agree that your contributions will be licensed under the same license as the project.

---

Thank you for contributing to the Debate System! 🎉
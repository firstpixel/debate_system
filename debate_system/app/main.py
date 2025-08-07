# debate_system/app/main.py

import os
import sys
import logging
from pathlib import Path
from app.config import load_config
from app.debate_manager import DebateManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """Main entry point for the debate system."""
    try:
        # Get config path from environment or use default
        config_path = os.getenv("DEBATE_CONFIG", "config/config_sample.yaml")
        
        # Check if config file exists
        if not os.path.exists(config_path):
            # Try some common locations
            possible_paths = [
                "config.yaml",
                "config/config.yaml", 
                "config/config_sample.yaml"
            ]
            
            config_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    config_path = path
                    break
            
            if config_path is None:
                logger.error("No configuration file found. Please provide a valid config file.")
                logger.info("Looking for: %s", " or ".join(possible_paths))
                sys.exit(1)
        
        logger.info(f"Loading configuration from: {config_path}")
        config = load_config(config_path)
        
        logger.info("Initializing debate manager...")
        debate = DebateManager(config)
        
        logger.info("Starting debate...")
        debate.start()
        
    except FileNotFoundError as e:
        logger.error(f"Configuration file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.info("Please run: pip install -r requirements-core.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Debate interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    run()

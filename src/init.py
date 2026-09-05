"""
ResolveAI System Initialization Helper
Handles environment verification, directory checks, and module loading.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
FRONTEND_DIR = BASE_DIR / "frontend"

def initialize_environment() -> bool:
    """
    Placeholder: Verify environment variables and data files readiness.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("[WARNING] GEMINI_API_KEY environment variable is not set.")
        return False
    return True

"""Application configuration."""

import os
from pathlib import Path

# Default scan path (can be overridden via environment variable)
REPO_BASE_PATH = os.environ.get("REPO_BASE_PATH", "/Users/olivier/Versioncontrol/local")

# App settings
APP_TITLE = "GIT LOCAL"
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "1899"))

from pathlib import Path


# ==========================================================
# PATHS
# ==========================================================
DATABASE_URL = "sqlite:///./omnifactory.db"
BASE_DIR = Path(__file__).resolve().parent.parent

STATIC_DIR = BASE_DIR / "static"

TEMPLATES_DIR = BASE_DIR / "templates"

DATA_DIR = BASE_DIR / "data"

OUTPUT_DIR = BASE_DIR / "output"

LOG_DIR = BASE_DIR / "logs"

# ==========================================================
# PROJECT
# ==========================================================

PROJECT_NAME = "OMNIFACTORY Platform"

VERSION = "1.0.0"

DEBUG = True

# ==========================================================
# DATABASE
# ==========================================================

DATABASE_URL = f"sqlite:///{BASE_DIR / 'omnifactory.db'}"

# ==========================================================
# SECURITY
# ==========================================================

SECRET_KEY = "CHANGE_ME"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ==========================================================
# API
# ==========================================================

API_PREFIX = "/api"

# ==========================================================
# BOT FACTORY
# ==========================================================

BOT_RUNTIME = BASE_DIR / "omni_factory_bots"

REGISTRY_FILE = BOT_RUNTIME / "config" / "registry.json"
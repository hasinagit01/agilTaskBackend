import os
from dotenv import load_dotenv

load_dotenv()

HOST        = os.environ.get("API_HOST",     "localhost")
PORT        = int(os.environ.get("API_PORT", 8000))
LOG_LEVEL   = os.environ.get("LOG_LEVEL",    "INFO").upper()
CORS_ORIGIN = os.environ.get("CORS_ORIGIN",  "*")
LOG_FILE    = os.environ.get("LOG_FILE",     "app.log")

SECRET_KEY                = os.environ.get("SECRET_KEY", "change-me-in-production")
ALGORITHM                 = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

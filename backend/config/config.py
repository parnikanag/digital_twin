import os

DEBUG = os.environ.get("DEBUG", "True").lower() in ("true", "1", "yes")
PORT = int(os.environ.get("PORT", 5000))

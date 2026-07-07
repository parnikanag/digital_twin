
import sys
import os

# Ensure the backend directory is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app

if __name__ == "__main__":
    app.run(debug=True)

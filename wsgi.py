# Import the Flask app directly from a file
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(__file__))

# Create a simple Flask app
from flask import Flask
app = Flask(__name__)

if __name__ == "__main__":
    app.run()
import sys
import os

# Добавляем директорию src в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from main import app

if __name__ == "__main__":
    app.run(debug=True)

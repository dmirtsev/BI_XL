import sys
import os

# Добавляем директорию src в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from main import dash_app

# Переменная server для Gunicorn
server = dash_app.server

if __name__ == "__main__":
    dash_app.run_server(debug=True)

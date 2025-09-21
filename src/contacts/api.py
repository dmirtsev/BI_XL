"""
API для модуля контактов.
"""
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from .core import import_contacts_from_excel

contacts_api = Blueprint('contacts_api', __name__)

UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@contacts_api.route('/upload', methods=['POST'])
def upload_file():
    """
    Принимает Excel-файл и запускает процесс импорта контактов.
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "Файл не найден"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "Файл не выбран"}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        result = import_contacts_from_excel(file_path)
        
        # Очистка после импорта
        os.remove(file_path)
        
        if result["status"] == "error":
            return jsonify(result), 500
        
        return jsonify(result), 200

    return jsonify({"status": "error", "message": "Непредвиденная ошибка"}), 500

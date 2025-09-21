"""
API для модуля аналитики.
"""
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from .core import import_orders_from_excel
from .models import init_db

# Создаем Blueprint для модуля
analytics_api = Blueprint('analytics_api', __name__)

# Папка для временного хранения загруженных файлов
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

@analytics_api.route('/upload', methods=['POST'])
def upload_file():
    """
    API-эндпоинт для загрузки Excel-файла с заказами.
    Принимает файл в POST-запросе и запускает процесс импорта.
    """
    if 'file' not in request.files:
        return jsonify({"error": "Файл не найден"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "Файл не выбран"}), 400

    if file and (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Инициализируем базу данных (создаем таблицы, если их нет)
        init_db()

        # Запускаем импорт
        result = import_orders_from_excel(file_path)

        # Удаляем временный файл
        os.remove(file_path)

        if result.get("status") == "error":
            return jsonify({"error": result.get("message")}), 500

        return jsonify(result), 200
    else:
        return jsonify({"error": "Неверный формат файла. Нужен .xls или .xlsx"}), 400

@analytics_api.route('/report', methods=['GET'])
def get_report():
    """
    Пример эндпоинта для получения отчета.
    (пока не реализован)
    """
    return jsonify({"message": "Отчет по аналитике (в разработке)"})

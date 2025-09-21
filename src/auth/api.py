"""
API endpoints for the authentication module.
"""
from flask import Blueprint, jsonify, request
from .core import get_user_status, authenticate_user

# Создаем Blueprint для модуля 'auth'
# Первый аргумент 'auth' - это имя Blueprint
# Второй аргумент __name__ - помогает Flask найти шаблоны и статические файлы
# url_prefix задается при регистрации Blueprint в main.py
auth_api = Blueprint('auth', __name__)

@auth_api.route('/status', methods=['GET'])
def status():
    """
    Returns the status of the authentication service.
    This is a simple health check endpoint.
    """
    return jsonify({"module": "auth", "status": "ok", "message": "Сервис аутентификации работает"})

@auth_api.route('/user/<int:user_id>', methods=['GET'])
def user_status(user_id: int):
    """
    Returns the status of a specific user.
    """
    status_info = get_user_status(user_id)
    return jsonify(status_info)

@auth_api.route('/login', methods=['POST'])
def login():
    """
    Authenticates a user based on JSON payload.
    Expects a JSON with "username" and "password".
    """
    data = request.get_json()
    if not data or 'username' not in data or 'password' not in data:
        return jsonify({"error": "Missing username or password"}), 400

    username = data['username']
    password = data['password']

    if authenticate_user(username, password):
        return jsonify({"message": "Authentication successful"}), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

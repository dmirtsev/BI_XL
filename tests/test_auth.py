import unittest
import sys
import os
import json

# Добавляем путь к 'src', чтобы можно было импортировать 'main'
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from main import app

class AuthModuleTestCase(unittest.TestCase):
    """Тесты для модуля аутентификации."""

    def setUp(self):
        """Настройка тестового клиента."""
        self.app = app.test_client()
        self.app.testing = True

    def test_auth_status(self):
        """Тест эндпоинта /api/auth/status."""
        response = self.app.get('/api/auth/status')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['module'], 'auth')
        self.assertEqual(data['status'], 'ok')

    def test_user_status_active(self):
        """Тест получения статуса активного пользователя."""
        response = self.app.get('/api/auth/user/1')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 1)
        self.assertEqual(data['status'], 'active')

    def test_user_status_inactive(self):
        """Тест получения статуса неактивного пользователя."""
        response = self.app.get('/api/auth/user/99')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['user_id'], 99)
        self.assertEqual(data['status'], 'inactive')

    def test_login_success(self):
        """Тест успешной аутентификации."""
        response = self.app.post('/api/auth/login',
                                 data=json.dumps({'username': 'admin', 'password': 'password123'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Authentication successful')

    def test_login_failure(self):
        """Тест неудачной аутентификации."""
        response = self.app.post('/api/auth/login',
                                 data=json.dumps({'username': 'admin', 'password': 'wrongpassword'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertEqual(data['message'], 'Invalid credentials')

    def test_login_missing_fields(self):
        """Тест запроса на аутентификацию с отсутствующими полями."""
        response = self.app.post('/api/auth/login',
                                 data=json.dumps({'username': 'admin'}),
                                 content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Missing username or password')

if __name__ == '__main__':
    unittest.main()

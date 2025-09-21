from flask import Flask, jsonify, render_template, render_template_string
from src.auth.api import auth_api
from src.analytics.api import analytics_api
from src.contacts.api import contacts_api
from src.product_grouping.api import product_grouping_api
from src.analytics.models import init_db
from src.dashboard.app import create_dash_app

app = Flask(__name__)

# --- Инициализация базы данных ---
# Создаем все таблицы перед первым запросом
@app.before_first_request
def setup_database():
    init_db()

# --- Инициализация Dash-приложения ---
dash_app = create_dash_app(app)

# --- Регистрация модулей ---
# Каждый модуль (Blueprint) регистрируется с уникальным префиксом URL.
app.register_blueprint(auth_api, url_prefix='/api/auth')
app.register_blueprint(analytics_api, url_prefix='/api/analytics')
app.register_blueprint(contacts_api, url_prefix='/api/contacts')
app.register_blueprint(product_grouping_api, url_prefix='/api/product-grouping')


# --- Основной интерфейс ---
@app.route('/')
def index():
    """
    Главная страница, которая отображает меню с доступом к модулям.
    """
    html_template = """
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Modular Web App</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f9f9f9; }
            .container { max-width: 800px; margin: auto; }
            .module { background-color: white; border: 1px solid #ccc; padding: 20px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            h1, h2 { color: #333; }
            button { padding: 10px 15px; border: none; background-color: #007BFF; color: white; border-radius: 5px; cursor: pointer; transition: background-color 0.3s; }
            button:hover { background-color: #0056b3; }
            input[type="file"] { margin-top: 10px; }
            pre { background-color: #f4f4f4; padding: 15px; border-radius: 5px; white-space: pre-wrap; word-wrap: break-word; border: 1px solid #ddd; }
            .result-container { margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Главное меню</h1>
            
            <!-- Модуль Аутентификации -->
            <div class="module">
                <h2>Модуль: Аутентификация</h2>
                <p>Этот модуль отвечает за проверку статуса аутентификации.</p>
                <button onclick="fetchData('/api/auth/status')">Проверить статус</button>
            </div>

            <!-- Модуль Аналитики -->
            <div class="module">
                <h2>Модуль: Аналитика Заказов</h2>
                <p>Загрузите Excel-файл с заказами для импорта в базу данных.</p>
                <form class="uploadForm" data-url="/api/analytics/upload">
                    <input type="file" name="file" accept=".xls,.xlsx">
                    <button type="submit">Загрузить заказы</button>
                </form>
            </div>

            <!-- Модуль Контактов -->
            <div class="module">
                <h2>Модуль: Контакты</h2>
                <p>Загрузите Excel-файл с контактами для импорта в базу данных.</p>
                <form class="uploadForm" data-url="/api/contacts/upload">
                    <input type="file" name="file" accept=".xls,.xlsx">
                    <button type="submit">Загрузить контакты</button>
                </form>
            </div>

            <!-- Модуль Дашборда -->
            <div class="module">
                <h2>Модуль: Аналитический Дашборд</h2>
                <p>Перейдите на страницу с интерактивными графиками и отчетами.</p>
                <a href="/dashboard/" target="_blank"><button>Открыть дашборд</button></a>
            </div>

            <!-- Модуль Группировки Продуктов -->
            <div class="module">
                <h2>Модуль: Группировка Продуктов</h2>
                <p>Перейдите на страницу для управления категориями продуктов.</p>
                <a href="/product-grouping" target="_blank"><button>Управление категориями</button></a>
            </div>

            <div class="result-container">
                <h3>Результат вызова API:</h3>
                <pre id="result">Здесь будет отображен результат...</pre>
            </div>
        </div>

        <script>
            function fetchData(url) {
                document.getElementById('result').textContent = 'Загрузка...';
                fetch(url)
                    .then(response => response.json())
                    .then(data => {
                        document.getElementById('result').textContent = JSON.stringify(data, null, 2);
                    })
                    .catch(error => {
                        document.getElementById('result').textContent = 'Ошибка: ' + error;
                    });
            }

            document.querySelectorAll('.uploadForm').forEach(form => {
                form.addEventListener('submit', function(event) {
                    event.preventDefault();
                    
                    const fileInput = form.querySelector('input[type="file"]');
                    const url = form.dataset.url;

                    if (fileInput.files.length === 0) {
                        document.getElementById('result').textContent = 'Пожалуйста, выберите файл.';
                        return;
                    }

                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);

                    document.getElementById('result').textContent = 'Загрузка и обработка файла...';

                    fetch(url, {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        if (!response.ok) {
                            // Попытка прочитать ошибку как JSON
                            return response.json().then(err => { 
                                // Используем сообщение из JSON, если оно есть
                                throw new Error(err.message || 'Неизвестная ошибка сервера'); 
                            });
                        }
                        return response.json();
                    })
                    .then(data => {
                        document.getElementById('result').textContent = 'Успешно!\\n' + JSON.stringify(data, null, 2);
                    })
                    .catch(error => {
                        document.getElementById('result').textContent = 'Ошибка: ' + error.message;
                    });
                });
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/product-grouping')
def product_grouping_page():
    """
    Отображает страницу для управления категориями продуктов.
    """
    return render_template('product_grouping.html')

if __name__ == '__main__':
    # Запускаем приложение. host='0.0.0.0' делает его доступным извне контейнера.
    app.run(host='0.0.0.0', port=8050, debug=True)

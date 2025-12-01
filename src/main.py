import io
import zipfile
import pytz
from datetime import datetime, date
import pandas as pd
import xlwt
from flask import Flask, jsonify, render_template, render_template_string, send_file
from sqlalchemy import func, inspect
from src.auth.api import auth_api
from src.analytics.api import analytics_api
from src.contacts.api import contacts_api
from src.product_grouping.api import product_grouping_api
from src.partner_analytics.api import partner_analytics_api
from src.analytics.models import init_db, SessionLocal, Order, engine
from src.contacts.models import Contact
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
app.register_blueprint(partner_analytics_api, url_prefix='/api/partner-analytics')

@app.route('/api/export/all')
def export_all_tables():
    """
    Экспортирует все таблицы базы данных в набор отдельных XLS-файлов (по файлу на таблицу) внутри zip-архива.
    """
    inspector = inspect(engine)
    table_names = inspector.get_table_names()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, mode='w', compression=zipfile.ZIP_DEFLATED) as zf:
        with engine.connect() as connection:
            for table in table_names:
                df = pd.read_sql_table(table, connection)
                excel_buffer = io.BytesIO()
                workbook = xlwt.Workbook()
                sheet = workbook.add_sheet(table[:31])  # ограничение Excel на длину имени листа

                # Заголовок
                for col_idx, col_name in enumerate(df.columns):
                    sheet.write(0, col_idx, col_name)

                # Данные
                for row_idx, row in enumerate(df.itertuples(index=False), start=1):
                    for col_idx, value in enumerate(row):
                        if pd.isna(value):
                            cell_value = ""
                        elif isinstance(value, (datetime, date)):
                            cell_value = value.strftime("%Y-%m-%d %H:%M:%S")
                        else:
                            cell_value = value
                        sheet.write(row_idx, col_idx, cell_value)

                workbook.save(excel_buffer)
                excel_buffer.seek(0)
                zf.writestr(f"{table}_{timestamp}.xls", excel_buffer.read())

    zip_buffer.seek(0)
    filename = f"analytics_exports_{timestamp}.zip"
    return send_file(
        zip_buffer,
        download_name=filename,
        as_attachment=True,
        mimetype="application/zip",
    )


# --- Основной интерфейс ---
@app.route('/')
def index():
    """
    Главная страница, которая отображает меню с доступом к модулям.
    """
    db = SessionLocal()
    try:
        max_order_date_utc = db.query(func.max(Order.creation_date)).scalar()
        max_contact_date_utc = db.query(func.max(Contact.creation_date)).scalar()
    finally:
        db.close()

    # Конвертация времени в московское
    moscow_tz = pytz.timezone('Europe/Moscow')
    
    max_order_date = None
    if max_order_date_utc:
        max_order_date = max_order_date_utc.replace(tzinfo=pytz.utc).astimezone(moscow_tz)

    max_contact_date = None
    if max_contact_date_utc:
        max_contact_date = max_contact_date_utc.replace(tzinfo=pytz.utc).astimezone(moscow_tz)

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
            
            <div class="stats-container" style="background-color: #e9ecef; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                <p><strong>Макс. дата создания заказа:</strong> {{ max_order_date.strftime('%d-%m-%Y %H:%M') if max_order_date else 'Нет данных' }}</p>
                <p><strong>Макс. дата создания контакта:</strong> {{ max_contact_date.strftime('%d-%m-%Y %H:%M') if max_contact_date else 'Нет данных' }}</p>
            </div>

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

            <!-- Модуль Выгрузки -->
            <div class="module">
                <h2>Выгрузка данных</h2>
                <p>Экспорт всех таблиц базы в отдельные XLS-файлы (zip-архив).</p>
                <a href="/api/export/all"><button>ВЫГРУЗКА</button></a>
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
    return render_template_string(
        html_template,
        max_order_date=max_order_date,
        max_contact_date=max_contact_date
    )

@app.route('/product-grouping')
def product_grouping_page():
    """
    Отображает страницу для управления категориями продуктов.
    """
    return render_template('product_grouping.html')

if __name__ == '__main__':
    # Запускаем приложение в режиме отладки для удобства разработки.
    # Указываем порт 5002, чтобы избежать конфликтов.
    app.run(debug=True, port=5002)

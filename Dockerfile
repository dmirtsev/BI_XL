# Используем официальный образ Python
FROM python:3.9-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл с зависимостями и устанавливаем их
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код проекта
COPY ./src ./src
COPY run.py .
COPY analytics.db .
COPY alembic.ini .
COPY migrations ./migrations

# Указываем порт, на котором будет работать приложение
EXPOSE 8050

# Запускаем приложение с помощью Gunicorn
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8050", "run:server"]

"""
Основная бизнес-логика для модуля аналитики.
"""
import pandas as pd
import numpy as np
from .models import SessionLocal, Order

# Словарь для сопоставления имен столбцов из Excel с полями модели Order
COLUMN_MAPPING = {
    "Идентификатор": "id",
    "Номер": "number",
    "Имя контакта": "contact_name",
    "Фамилия контакта": "contact_surname",
    "Email контакта": "contact_email",
    "Ответственный": "responsible_person",
    "Содержимое": "content",
    "Статус": "status",
    "Общая сумма": "total_amount",
    "Оплаченная сумма": "paid_amount",
    "Дата создания": "creation_date",
    "Дата оплаты": "payment_date",
    "Валюта": "currency",
    "Теги": "tags",
    "Сумма скидки": "discount_amount",
    "Доход": "income",
    "Комиссия": "commission",
    "Идентификатор партнера": "partner_id",
    "Email партнера": "partner_email",
    "Комиссия партнера": "partner_commission",
    "Телефон контакта": "contact_phone",
    "Идентификатор контакта": "contact_id",
    "UTM Campaign": "utm_campaign",
    "UTM Content": "utm_content",
    "UTM Medium": "utm_medium",
    "UTM Source": "utm_source",
    "UTM Term": "utm_term",
    "Дата заказа в ГК": "gc_order_date",
}

def import_orders_from_excel(file_path: str):
    """
    Импортирует или обновляет заказы в базе данных из Excel-файла.

    Args:
        file_path (str): Путь к Excel-файлу (.xls или .xlsx).
    """
    try:
        # Используем openpyxl, так как работаем с .xlsx
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        # Если openpyxl не сработает, можно попробовать другие движки
        # или вернуть ошибку, что формат не поддерживается.
        print(f"Ошибка чтения файла: {e}")
        return {"status": "error", "message": str(e)}

    # Переименовываем столбцы для соответствия модели
    df = df.rename(columns=COLUMN_MAPPING)

    # Преобразуем столбцы с датами
    date_columns = ['creation_date', 'payment_date', 'gc_order_date']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    # Заменяем NaN (для чисел) и NaT (для дат) на None.
    # Этот метод более надежен, чем df.where().
    df = df.replace({np.nan: None, pd.NaT: None})

    db = SessionLocal()
    updated_count = 0
    created_count = 0

    try:
        for _, row in df.iterrows():
            order_id = row.get('id')
            if not order_id:
                continue

            # Ищем существующий заказ
            existing_order = db.query(Order).filter(Order.id == order_id).first()
            
            order_data = row.to_dict()

            if existing_order:
                # Обновляем существующий заказ
                for key, value in order_data.items():
                    if hasattr(existing_order, key):
                        setattr(existing_order, key, value)
                updated_count += 1
            else:
                # Создаем новый заказ
                new_order = Order(**order_data)
                db.add(new_order)
                created_count += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        print(f"Ошибка при работе с базой данных: {e}")
        return {"status": "error", "message": f"DB error: {e}"}
    finally:
        db.close()

    return {
        "status": "success",
        "created": created_count,
        "updated": updated_count
    }

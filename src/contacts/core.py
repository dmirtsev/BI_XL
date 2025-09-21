"""
Основная бизнес-логика для модуля контактов.
"""
import pandas as pd
import numpy as np
from src.analytics.models import SessionLocal  # Используем ту же сессию
from .models import Contact

# Словарь для сопоставления имен столбцов из Excel с полями модели Contact
COLUMN_MAPPING = {
    "Идентификатор": "id",
    "Полное имя": "full_name",
    "Имя": "first_name",
    "Отчество": "middle_name",
    "Фамилия": "last_name",
    "Email": "email",
    "Email адреса": "emails",
    "Телефон": "phone",
    "Телефоны": "phones",
    "Страна": "country",
    "Город": "city",
    "Регион": "region",
    "Теги": "tags",
    "Группы": "groups",
    "Дата создания": "creation_date",
    "День рождения": "birthday",
    "Последний раз онлайн": "last_online",
    "Последняя активность": "last_activity",
    "Сумма оплат": "total_paid",
    "Геймификация. Баллы": "gamification_score",
    "Баланс бонусов": "bonus_balance",
    "Партнер ID": "partner_id",
    "Первая utm_source метка": "first_utm_source",
    "Последняя utm_source метка": "last_utm_source",
    "tg_id": "tg_id",
}

def import_contacts_from_excel(file_path: str):
    """
    Импортирует или обновляет контакты в базе данных из Excel-файла.
    """
    try:
        df = pd.read_excel(file_path, engine='openpyxl')
    except Exception as e:
        return {"status": "error", "message": f"Ошибка чтения файла: {e}"}

    df = df.rename(columns=COLUMN_MAPPING)

    date_columns = ['creation_date', 'birthday', 'last_online', 'last_activity']
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

    df = df.replace({np.nan: None, pd.NaT: None})

    db = SessionLocal()
    updated_count = 0
    created_count = 0

    try:
        for _, row in df.iterrows():
            contact_id = row.get('id')
            if not contact_id:
                continue

            existing_contact = db.query(Contact).filter(Contact.id == contact_id).first()
            contact_data = row.to_dict()

            # Убираем ключи, которых нет в модели, чтобы избежать ошибок
            valid_keys = [c.name for c in Contact.__table__.columns]
            filtered_data = {k: v for k, v in contact_data.items() if k in valid_keys}

            if existing_contact:
                for key, value in filtered_data.items():
                    setattr(existing_contact, key, value)
                updated_count += 1
            else:
                new_contact = Contact(**filtered_data)
                db.add(new_contact)
                created_count += 1
        
        db.commit()
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": f"DB error: {e}"}
    finally:
        db.close()

    return {
        "status": "success",
        "created": created_count,
        "updated": updated_count
    }

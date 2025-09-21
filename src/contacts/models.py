"""
Модели данных для модуля контактов.
"""
from sqlalchemy import Column, String, Float, DateTime, Text
from src.analytics.models import Base  # Используем тот же Base, что и для заказов

class Contact(Base):
    """
    Модель SQLAlchemy, представляющая контакт в базе данных.
    """
    __tablename__ = "contacts"

    # --- Основная информация ---
    id = Column(String, primary_key=True, index=True)
    full_name = Column(String)
    first_name = Column(String)
    middle_name = Column(String)
    last_name = Column(String)

    # --- Контактные данные ---
    email = Column(String, index=True)
    emails = Column(Text)  # Для хранения нескольких email, например, через запятую
    phone = Column(String)
    phones = Column(Text)  # Для хранения нескольких телефонов

    # --- География ---
    country = Column(String)
    city = Column(String)
    region = Column(String)

    # --- Метаданные ---
    tags = Column(Text)
    groups = Column(Text)
    creation_date = Column(DateTime)
    birthday = Column(DateTime)
    last_online = Column(DateTime)
    last_activity = Column(DateTime)

    # --- Финансы и геймификация ---
    total_paid = Column(Float)
    gamification_score = Column(Float)
    bonus_balance = Column(Float)

    # --- Маркетинг и партнеры ---
    partner_id = Column(String, index=True)
    first_utm_source = Column(String)
    last_utm_source = Column(String)
    tg_id = Column(String, index=True)

    def __repr__(self):
        return f"<Contact(id={self.id}, full_name='{self.full_name}')>"

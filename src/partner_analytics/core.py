"""
Основная бизнес-логика для модуля аналитики по партнерам.
"""
from sqlalchemy.orm import Session
from . import queries

def get_partner_analytics(db: Session, start_date: str, end_date: str):
    """
    Возвращает агрегированные данные по партнерам за указанный период.
    """
    return queries.get_partner_analytics_data(db, start_date, end_date)

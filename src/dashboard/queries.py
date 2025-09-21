"""
Функции для выполнения SQL-запросов к базе данных для дашборда.
"""
import pandas as pd
from sqlalchemy import func
from src.analytics.models import SessionLocal, Order

def get_sales_by_day(start_date, end_date):
    """
    Возвращает суммарный доход по дням за указанный период.
    """
    db = SessionLocal()
    try:
        query = (
            db.query(
                func.date(Order.creation_date).label('date'),
                func.sum(Order.income).label('total_sales')
            )
            .filter(Order.creation_date.between(start_date, end_date))
            .group_by(func.date(Order.creation_date))
            .order_by(func.date(Order.creation_date))
        )
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_unique_products():
    """
    Возвращает список уникальных наименований продуктов.
    """
    db = SessionLocal()
    try:
        # Извлекаем уникальные, не-None значения и сортируем их
        products = db.query(Order.content).filter(Order.content.isnot(None)).distinct().order_by(Order.content).all()
        # Преобразуем результат в список строк
        return [product[0] for product in products]
    finally:
        db.close()

def get_sales_by_product(product_names, start_date, end_date):
    """
    Возвращает дневной и накопительный доход для указанных продуктов и периода.
    """
    db = SessionLocal()
    try:
        # Подзапрос для агрегации дохода по дням для конкретных продуктов
        daily_sales_subquery = (
            db.query(
                func.date(Order.creation_date).label('date'),
                func.sum(Order.income).label('daily_sales')
            )
            .filter(Order.content.in_(product_names))
            .filter(Order.creation_date.between(start_date, end_date))
            .group_by(func.date(Order.creation_date))
        ).subquery()

        # Основной запрос с использованием оконной функции для расчета накопительной суммы
        query = (
            db.query(
                daily_sales_subquery.c.date,
                daily_sales_subquery.c.daily_sales,
                func.sum(daily_sales_subquery.c.daily_sales).over(
                    order_by=daily_sales_subquery.c.date
                ).label('cumulative_sales')
            )
            .order_by(daily_sales_subquery.c.date)
        )
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

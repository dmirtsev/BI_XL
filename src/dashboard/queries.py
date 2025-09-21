"""
Функции для выполнения SQL-запросов к базе данных для дашборда.
"""
import pandas as pd
from sqlalchemy import func, case
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

def get_product_summary(product_names, start_date, end_date):
    """
    Возвращает сводную информацию по продуктам: количество заявок,
    количество оплат, общий доход и средний чек.
    """
    db = SessionLocal()
    try:
        paid_orders_case = case((Order.income > 0, 1), else_=0)
        
        query = (
            db.query(
                Order.content.label('product'),
                func.count(Order.id).label('total_orders'),
                func.sum(paid_orders_case).label('paid_orders'),
                func.sum(Order.income).label('total_income'),
                func.avg(case((Order.income > 0, Order.income))).label('average_check')
            )
            .filter(Order.content.in_(product_names))
            .filter(Order.creation_date.between(start_date, end_date))
            .group_by(Order.content)
            .order_by(Order.content)
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
        # Подзапрос для агрегации данных по дням для конкретных продуктов
        daily_agg_subquery = (
            db.query(
                func.date(Order.creation_date).label('date'),
                func.sum(Order.income).label('daily_sales'),
                func.count(Order.id).label('total_orders'),
                func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
            )
            .filter(Order.content.in_(product_names))
            .filter(Order.creation_date.between(start_date, end_date))
            .group_by(func.date(Order.creation_date))
        ).subquery()

        # Основной запрос с использованием оконной функции для расчета накопительной суммы
        query = (
            db.query(
                daily_agg_subquery.c.date,
                daily_agg_subquery.c.daily_sales,
                daily_agg_subquery.c.total_orders,
                daily_agg_subquery.c.paid_orders,
                func.sum(daily_agg_subquery.c.daily_sales).over(
                    order_by=daily_agg_subquery.c.date
                ).label('cumulative_sales')
            )
            .order_by(daily_agg_subquery.c.date)
        )
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_paid_products_summary(start_date, end_date):
    """
    Возвращает сводку по продуктам, у которых были оплаты за период.
    """
    db = SessionLocal()
    try:
        paid_orders_case = case((Order.income > 0, 1), else_=0)
        
        query = (
            db.query(
                Order.content.label('product'),
                func.count(Order.id).label('total_orders'),
                func.sum(paid_orders_case).label('paid_orders')
            )
            .filter(Order.creation_date.between(start_date, end_date))
            .group_by(Order.content)
            .having(func.sum(paid_orders_case) > 0)
            .order_by(Order.content)
        )
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

"""
Функции для выполнения SQL-запросов к базе данных для дашборда.
"""
import pandas as pd
from sqlalchemy import func, case
from src.analytics.models import SessionLocal, Order
from src.product_grouping.models import Product, ProductCategory, product_category_association

def get_sales_by_day(start_date, end_date, category_id=None):
    """
    Возвращает суммарный доход по дням за указанный период.
    Фильтрует по категории, если она указана.
    """
    db = SessionLocal()
    try:
        query = db.query(
            func.date(Order.creation_date).label('date'),
            func.sum(Order.income).label('total_sales')
        ).filter(Order.creation_date.between(start_date, end_date))

        if category_id:
            # Присоединяем продукты и их категории для фильтрации
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id == category_id)

        query = query.group_by(func.date(Order.creation_date)).order_by(func.date(Order.creation_date))
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_category_revenue_by_period(start_date, end_date):
    """
    Возвращает доход по каждой категории продуктов за указанный период.
    """
    db = SessionLocal()
    try:
        query = db.query(
            ProductCategory.name.label('category_name'),
            func.sum(Order.income).label('total_revenue')
        ).select_from(Order)\
         .join(Product, Order.content == Product.name)\
         .join(product_category_association, Product.id == product_category_association.c.product_id)\
         .join(ProductCategory, ProductCategory.id == product_category_association.c.category_id)\
         .filter(Order.creation_date.between(start_date, end_date))\
         .filter(Order.income > 0)\
         .group_by(ProductCategory.name)\
         .order_by(func.sum(Order.income).desc())

        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_product_summary(product_names, start_date, end_date, category_id=None):
    """
    Возвращает сводную информацию по продуктам.
    Фильтрует по категории, если она указана.
    """
    db = SessionLocal()
    try:
        paid_orders_case = case((Order.income > 0, 1), else_=0)
        
        query = db.query(
            Order.content.label('product'),
            func.count(Order.id).label('total_orders'),
            func.sum(paid_orders_case).label('paid_orders'),
            func.sum(Order.income).label('total_income'),
            func.avg(case((Order.income > 0, Order.income))).label('average_check')
        ).filter(Order.creation_date.between(start_date, end_date))

        if category_id:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id == category_id)
        
        # Если указаны конкретные продукты, фильтруем по ним
        if product_names:
            query = query.filter(Order.content.in_(product_names))

        query = query.group_by(Order.content).order_by(Order.content)
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_unique_products(category_id=None):
    """
    Возвращает список уникальных продуктов, опционально фильтруя по категории.
    """
    db = SessionLocal()
    try:
        query = db.query(Order.content).filter(Order.content.isnot(None))

        if category_id:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id == category_id)

        products = query.distinct().order_by(Order.content).all()
        return [product[0] for product in products]
    finally:
        db.close()

def get_categories():
    """
    Возвращает список всех категорий продуктов.
    """
    db = SessionLocal()
    try:
        categories = db.query(ProductCategory).order_by(ProductCategory.name).all()
        return [{"label": cat.name, "value": cat.id} for cat in categories]
    finally:
        db.close()

def get_sales_by_product(product_names, start_date, end_date, category_id=None):
    """
    Возвращает дневной и накопительный доход для указанных продуктов и периода.
    """
    db = SessionLocal()
    try:
        # Базовый запрос для агрегации
        daily_agg_query = db.query(
            func.date(Order.creation_date).label('date'),
            func.sum(Order.income).label('daily_sales'),
            func.count(Order.id).label('total_orders'),
            func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
        ).filter(Order.creation_date.between(start_date, end_date))

        # Применяем фильтры
        if product_names:
            daily_agg_query = daily_agg_query.filter(Order.content.in_(product_names))
        
        if category_id:
            daily_agg_query = daily_agg_query.join(Product, Order.content == Product.name)\
                                             .join(product_category_association)\
                                             .filter(product_category_association.c.category_id == category_id)

        # Группируем и создаем подзапрос
        daily_agg_subquery = daily_agg_query.group_by(func.date(Order.creation_date)).subquery()

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

def get_paid_products_summary(start_date, end_date, category_id=None):
    """
    Возвращает сводку по продуктам с оплатами, опционально фильтруя по категории.
    """
    db = SessionLocal()
    try:
        paid_orders_case = case((Order.income > 0, 1), else_=0)
        
        query = db.query(
            Order.content.label('product'),
            func.count(Order.id).label('total_orders'),
            func.sum(paid_orders_case).label('paid_orders'),
            func.sum(Order.income).label('total_income')
        ).filter(Order.creation_date.between(start_date, end_date))

        if category_id:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id == category_id)

        query = query.group_by(Order.content)\
                     .having(func.sum(paid_orders_case) > 0)\
                     .order_by(Order.content)
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

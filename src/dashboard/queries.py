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

def get_monthly_sales_by_category(start_date, end_date, category_ids=None, product_names=None):
    """
    Возвращает суммарный доход по месяцам в разрезе категорий за указанный период.
    """
    db = SessionLocal()
    try:
        query = db.query(
            func.strftime('%Y-%m', Order.creation_date).label('month'),
            ProductCategory.name.label('category'),
            func.sum(Order.income).label('total_sales'),
            func.count(Order.id).label('total_orders'),
            func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
        ).join(Product, Order.content == Product.name)\
         .join(product_category_association)\
         .join(ProductCategory)\
         .filter(Order.income > 0)

        if start_date and end_date:
            query = query.filter(Order.creation_date.between(start_date, end_date))

        if category_ids:
            query = query.filter(ProductCategory.id.in_(category_ids))
        
        if product_names:
            query = query.filter(Order.content.in_(product_names))

        query = query.group_by('month', 'category').order_by('month', 'category')
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_monthly_sales_by_product(start_date, end_date, category_ids=None, product_names=None):
    """
    Возвращает суммарный доход по месяцам в разрезе продуктов за указанный период,
    опционально фильтруя по категориям и продуктам.
    """
    db = SessionLocal()
    try:
        query = db.query(
            func.strftime('%Y-%m', Order.creation_date).label('month'),
            Order.content.label('product'),
            func.sum(Order.income).label('total_sales'),
            func.count(Order.id).label('total_orders'),
            func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
        ).filter(Order.income > 0)

        if start_date and end_date:
            query = query.filter(Order.creation_date.between(start_date, end_date))

        if category_ids:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id.in_(category_ids))
        
        if product_names:
            query = query.filter(Order.content.in_(product_names))

        query = query.group_by('month', 'product').order_by('month', 'product')
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_monthly_sales(start_date, end_date, category_ids=None, product_names=None):
    """
    Возвращает суммарный доход по месяцам за указанный период,
    опционально фильтруя по категориям и продуктам.
    """
    db = SessionLocal()
    try:
        query = db.query(
            func.strftime('%Y-%m', Order.creation_date).label('month'),
            func.sum(Order.income).label('total_sales'),
            func.count(Order.id).label('total_orders'),
            func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
        ).filter(Order.income > 0)

        if start_date and end_date:
            query = query.filter(Order.creation_date.between(start_date, end_date))

        if category_ids:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)\
                         .filter(product_category_association.c.category_id.in_(category_ids))
        
        if product_names:
            query = query.filter(Order.content.in_(product_names))

        query = query.group_by('month').order_by('month')
        
        df = pd.read_sql(query.statement, db.bind)
        return df
    finally:
        db.close()

def get_category_revenue_by_period(start_date, end_date, excluded_category_ids=None, included_category_ids=None):
    """
    Возвращает доход по каждой категории продуктов за указанный период,
    исключая категории из списка excluded_category_ids.
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
         .filter(Order.income > 0)

        if start_date and end_date:
            query = query.filter(Order.creation_date.between(start_date, end_date))

        if included_category_ids:
            query = query.filter(ProductCategory.id.in_(included_category_ids))
            
        if excluded_category_ids:
            query = query.filter(ProductCategory.id.notin_(excluded_category_ids))

        query = query.group_by(ProductCategory.name)\
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
    category_id может быть одиночным значением или списком.
    """
    db = SessionLocal()
    try:
        query = db.query(Order.content).filter(Order.content.isnot(None))

        if category_id:
            query = query.join(Product, Order.content == Product.name)\
                         .join(product_category_association)
            
            # Проверяем, является ли category_id списком и не пуст ли он
            if isinstance(category_id, list) and category_id:
                query = query.filter(product_category_association.c.category_id.in_(category_id))
            # Проверяем, является ли category_id одиночным числом
            elif isinstance(category_id, int):
                query = query.filter(product_category_association.c.category_id == category_id)

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
    Возвращает дневной и накопительный доход для указанных продуктов и периода,
    а также максимальную дату создания заказа в этом периоде.
    """
    db = SessionLocal()
    try:
        # --- Запрос для получения максимальной даты ---
        max_date_query = db.query(func.max(Order.creation_date)).filter(
            Order.creation_date.between(start_date, end_date)
        )

        # --- Общий запрос для данных ---
        base_query = db.query(Order).filter(Order.creation_date.between(start_date, end_date))

        # Применяем фильтры к обоим запросам
        if product_names:
            base_query = base_query.filter(Order.content.in_(product_names))
            max_date_query = max_date_query.filter(Order.content.in_(product_names))
        
        if category_id:
            join_clause = Product.__table__.join(
                product_category_association,
                Product.id == product_category_association.c.product_id
            )
            base_query = base_query.join(join_clause, Product.name == Order.content)\
                                   .filter(product_category_association.c.category_id == category_id)
            max_date_query = max_date_query.join(join_clause, Product.name == Order.content)\
                                           .filter(product_category_association.c.category_id == category_id)

        # Выполняем запрос на максимальную дату
        max_creation_date = max_date_query.scalar()

        # --- Запрос для агрегации данных (как и раньше) ---
        daily_agg_subquery = base_query.with_entities(
            func.date(Order.creation_date).label('date'),
            func.sum(Order.income).label('daily_sales'),
            func.count(Order.id).label('total_orders'),
            func.sum(case((Order.income > 0, 1), else_=0)).label('paid_orders')
        ).group_by(func.date(Order.creation_date)).subquery()

        # Основной запрос с оконной функцией
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
        
        return df, max_creation_date
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

"""
Бизнес-логика для модуля группировки продуктов.
"""
from sqlalchemy.orm import Session
from src.analytics.models import Order, SessionLocal
from .models import Product

def sync_products_from_orders():
    """
    Синхронизирует таблицу продуктов с данными из заказов.
    Добавляет новые уникальные продукты из Order.content в таблицу Product.
    """
    db: Session = SessionLocal()
    try:
        # Получаем все уникальные наименования продуктов из заказов
        order_products = db.query(Order.content).filter(Order.content.isnot(None)).distinct().all()
        order_product_names = {name for (name,) in order_products}

        # Получаем все существующие продукты из нашей новой таблицы
        existing_products = db.query(Product.name).all()
        existing_product_names = {name for (name,) in existing_products}

        # Определяем, какие продукты нужно добавить
        new_product_names = order_product_names - existing_product_names

        if new_product_names:
            new_products = [Product(name=name) for name in new_product_names]
            db.add_all(new_products)
            db.commit()
            return {"status": "success", "added": len(new_products)}
        
        return {"status": "success", "added": 0}
    except Exception as e:
        db.rollback()
        return {"status": "error", "message": str(e)}
    finally:
        db.close()

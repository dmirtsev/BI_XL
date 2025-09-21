"""
API для модуля группировки продуктов.
"""
from flask import Blueprint, jsonify, request
from sqlalchemy.orm import Session
from src.analytics.models import SessionLocal
from .models import Product, ProductCategory
from .core import sync_products_from_orders

product_grouping_api = Blueprint('product_grouping_api', __name__)

@product_grouping_api.route('/products', methods=['GET'])
def get_products():
    """Возвращает список всех продуктов и их категорий."""
    db: Session = SessionLocal()
    try:
        products = db.query(Product).all()
        result = [
            {
                "id": p.id,
                "name": p.name,
                "categories": [c.name for c in p.categories]
            } for p in products
        ]
        return jsonify(result)
    finally:
        db.close()

@product_grouping_api.route('/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    """Возвращает детали одного продукта, включая его категории."""
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return jsonify({"error": "Product not found"}), 404
        
        result = {
            "id": product.id,
            "name": product.name,
            "categories": [c.name for c in product.categories]
        }
        return jsonify(result)
    finally:
        db.close()

@product_grouping_api.route('/categories', methods=['GET', 'POST'])
def handle_categories():
    """Создает новую категорию или возвращает список всех категорий."""
    db: Session = SessionLocal()
    try:
        if request.method == 'POST':
            data = request.get_json()
            if not data or 'name' not in data:
                return jsonify({"error": "Missing category name"}), 400
            
            new_category = ProductCategory(name=data['name'])
            db.add(new_category)
            db.commit()
            return jsonify({"id": new_category.id, "name": new_category.name}), 201

        # GET request
        categories = db.query(ProductCategory).all()
        return jsonify([{"id": c.id, "name": c.name} for c in categories])
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@product_grouping_api.route('/categories/<int:category_id>', methods=['DELETE'])
def delete_category(category_id):
    """Удаляет категорию."""
    db: Session = SessionLocal()
    try:
        category = db.query(ProductCategory).filter(ProductCategory.id == category_id).first()
        if not category:
            return jsonify({"error": "Category not found"}), 404
        
        db.delete(category)
        db.commit()
        return jsonify({"message": "Category deleted"}), 200
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@product_grouping_api.route('/products/<int:product_id>/assign-categories', methods=['POST'])
def assign_categories_to_product(product_id):
    """Присваивает категории продукту."""
    db: Session = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return jsonify({"error": "Product not found"}), 404

        data = request.get_json()
        category_ids = data.get('category_ids', [])
        
        # Находим объекты категорий
        categories = db.query(ProductCategory).filter(ProductCategory.id.in_(category_ids)).all()
        
        # Обновляем связь
        product.categories = categories
        db.commit()
        
        return jsonify({"message": "Categories assigned successfully"})
    except Exception as e:
        db.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        db.close()

@product_grouping_api.route('/products/sync', methods=['POST'])
def sync_products():
    """Запускает синхронизацию продуктов из заказов."""
    result = sync_products_from_orders()
    if result["status"] == "error":
        return jsonify(result), 500
    return jsonify(result)

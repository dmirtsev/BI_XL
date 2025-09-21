"""
Модели базы данных для группировки продуктов.
"""
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship
from src.analytics.models import Base  # Используем ту же базовую модель

# Ассоциативная таблица для связи "многие-ко-многим" между продуктами и категориями
product_category_association = Table(
    'product_category_association', Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('category_id', Integer, ForeignKey('product_categories.id'))
)

class Product(Base):
    """
    Модель для хранения уникальных продуктов.
    """
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    
    # Связь "многие-ко-многим" с категориями
    categories = relationship(
        "ProductCategory",
        secondary=product_category_association,
        back_populates="products"
    )

class ProductCategory(Base):
    """
    Модель для хранения категорий продуктов.
    """
    __tablename__ = 'product_categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # Связь "многие-ко-многим" с продуктами
    products = relationship(
        "Product",
        secondary=product_category_association,
        back_populates="categories"
    )

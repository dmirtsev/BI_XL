"""
Модели данных для модуля аналитики.
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# --- Настройка базы данных ---
# Используем SQLite, которая хранит базу данных в одном файле.
DATABASE_URL = "sqlite:///./analytics.db"

# Создаем "движок" для подключения к базе
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Создаем сессию для взаимодействия с базой
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для всех моделей
Base = declarative_base()


# --- Модель данных для Заказов ---
class Order(Base):
    """
    Модель SQLAlchemy, представляющая заказ в базе данных.
    """
    __tablename__ = "orders"

    # Уникальный идентификатор из Excel-файла будет основным ключом.
    # Тип String, так как ID могут быть нечисловыми.
    id = Column(String, primary_key=True, index=True)
    
    number = Column(String)
    contact_name = Column(String)
    contact_surname = Column(String)
    recipient_last_name = Column(String) # Фамилия получателя
    contact_email = Column(String)
    responsible_person = Column(String)
    content = Column(Text)
    status = Column(String)
    total_amount = Column(Float)
    paid_amount = Column(Float)
    creation_date = Column(DateTime)
    payment_date = Column(DateTime)
    currency = Column(String)
    tags = Column(String)
    discount_amount = Column(Float)
    income = Column(Float)
    commission = Column(Float)
    partner_id = Column(String)
    partner_email = Column(String)
    partner_commission = Column(Float)
    contact_phone = Column(String)
    # Тип String, так как ID могут быть нечисловыми.
    contact_id = Column(String)
    utm_campaign = Column(String)
    utm_content = Column(String)
    utm_medium = Column(String)
    utm_source = Column(String)
    utm_term = Column(String)
    gc_order_date = Column(DateTime)

    def __repr__(self):
        return f"<Order(id={self.id}, number='{self.number}')>"

def init_db():
    """
    Создает все таблицы в базе данных.
    """
    Base.metadata.create_all(bind=engine)

import sys
from pathlib import Path

# Добавляем корневую папку проекта в sys.path
project_root = Path(__file__).parent.resolve()
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from src.analytics.models import Order
from src.contacts.models import Contact

def check_db_counts():
    """
    Подключается к базе данных и выводит количество записей в таблицах.
    """
    DATABASE_URL = "sqlite:///./analytics.db"
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        inspector = inspect(engine)
        
        # Проверка таблицы 'orders'
        if inspector.has_table("orders"):
            orders_count = db.query(Order).count()
            print(f"Количество записей в таблице 'orders': {orders_count}")
        else:
            print("Таблица 'orders' не найдена.")

        # Проверка таблицы 'contacts'
        if inspector.has_table("contacts"):
            contacts_count = db.query(Contact).count()
            print(f"Количество записей в таблице 'contacts': {contacts_count}")
        else:
            print("Таблица 'contacts' не найдена.")
            
    except Exception as e:
        print(f"Произошла ошибка при подключении к базе данных: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_db_counts()

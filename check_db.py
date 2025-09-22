from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.analytics.models import Order
from src.contacts.models import Contact

# Подключение к базе данных
DATABASE_URL = "sqlite:///analytics.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_ids():
    db = SessionLocal()
    try:
        target_id = "PH11ga6ev0emd7JNsTvsqg"

        # Проверка в контактах (оставляем как есть или убираем, если не нужно)
        contact = db.query(Contact).filter(Contact.id == target_id).first()
        if contact:
            print(f"Найден контакт с ID {target_id}: {contact}")
        else:
            print(f"Контакт с ID {target_id} не найден.")

        # Проверка в заказах по utm_source
        orders = db.query(Order).filter(Order.utm_source == target_id).all()
        if orders:
            print(f"Найдены заказы с utm_source {target_id}:")
            for order in orders:
                print(order)
        else:
            print(f"Заказы с utm_source {target_id} не найдены.")

    finally:
        db.close()

if __name__ == "__main__":
    check_ids()

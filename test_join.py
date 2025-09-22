import sqlite3

def count_orders():
    conn = sqlite3.connect('analytics.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM orders;")
    count = cursor.fetchone()[0]

    print(f"В таблице 'orders' {count} записей.")

    conn.close()

if __name__ == '__main__':
    count_orders()

"""
SQL-запросы для модуля аналитики по партнерам.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

def get_partner_analytics_data(db: Session, start_date: str, end_date: str, exclude_common: bool = False):
    """
    Выполняет SQL-запрос для получения агрегированных данных по партнерам.
    """
    params = {"start_date": start_date, "end_date": end_date}
    
    query_sql = """
        SELECT
            COALESCE(c.full_name, 'Общий источник') AS partner,
            o.utm_source,
            COUNT(o.id) AS order_count,
            SUM(o.income) AS total_income
        FROM
            orders o
        LEFT JOIN
            contacts c ON o.utm_source = c.id
        WHERE
            DATE(o.creation_date) >= :start_date AND DATE(o.creation_date) <= :end_date
    """
    
    # Динамически добавляем условие для исключения "Общего источника"
    if exclude_common:
        query_sql += " AND COALESCE(c.full_name, 'Общий источник') != 'Общий источник'"

    query_sql += """
        GROUP BY
            partner, o.utm_source
        ORDER BY
            total_income DESC;
    """
    
    query = text(query_sql)
    result = db.execute(query, params)
    return result.fetchall()

"""
API для модуля аналитики по партнерам.
"""
from flask import Blueprint, jsonify, request
from src.analytics.models import SessionLocal
from . import core

partner_analytics_api = Blueprint('partner_analytics_api', __name__)

@partner_analytics_api.route('/', methods=['GET'])
def get_partner_analytics_data():
    """
    Возвращает аналитику по партнерам за указанный период.
    """
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    db = SessionLocal()
    try:
        data = core.get_partner_analytics(db, start_date, end_date)
        # Преобразуем каждую строку в словарь
        result = [dict(row._mapping) for row in data]
        return jsonify(result)
    finally:
        db.close()

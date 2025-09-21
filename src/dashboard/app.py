"""
Инициализация и настройка Dash-приложения.
"""
from dash import Dash
from .layout import layout
from . import callbacks

def create_dash_app(flask_app):
    """
    Создает и настраивает Dash-приложение, интегрированное с Flask.
    """
    dash_app = Dash(
        server=flask_app,
        url_base_pathname='/dashboard/',
        suppress_callback_exceptions=True
    )
    
    dash_app.layout = layout
    callbacks.register_callbacks(dash_app)
    
    return dash_app

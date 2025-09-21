"""
Callbacks для Dash-приложения.
Здесь определяется интерактивная логика дашборда.
"""
from dash import html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .queries import get_sales_by_day, get_unique_products, get_sales_by_product, get_product_summary

def register_callbacks(app):
    """
    Регистрирует все callbacks для Dash-приложения.
    """
    # Callback для обновления графика на первой вкладке (Общая динамика)
    @app.callback(
        Output('sales-by-day-chart', 'figure'),
        [Input('start-date-picker-general', 'date'),
         Input('end-date-picker-general', 'date')]
    )
    def update_general_sales_chart(start_date, end_date):
        df = get_sales_by_day(start_date, end_date)
        if df.empty:
            return _create_empty_figure("Нет данных за выбранный период")
            
        fig = px.line(
            df, x='date', y='total_sales', title='Динамика дохода по дням',
            labels={'date': 'Дата', 'total_sales': 'Сумма дохода'}
        )
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
        return fig

    # Callback для загрузки списка продуктов во второй вкладке
    @app.callback(
        Output('product-dropdown', 'options'),
        Input('tabs-main', 'value')
    )
    def update_product_dropdown(tab):
        if tab == 'tab-product':
            products = get_unique_products()
            return [{'label': i, 'value': i} for i in products]
        raise PreventUpdate

    # Callback для обновления графика и таблицы на второй вкладке (Отчет по продуктам)
    @app.callback(
        [Output('sales-by-product-chart', 'figure'),
         Output('product-sales-table', 'data'),
         Output('product-sales-table', 'columns'),
         Output('product-summary-table', 'data'),
         Output('product-summary-table', 'columns'),
         Output('conversion-summary-div', 'children')],
        [Input('product-dropdown', 'value'),
         Input('start-date-picker-product', 'date'),
         Input('end-date-picker-product', 'date')],
        [State('festival-income-input', 'value')]
    )
    def update_product_sales_chart(product_names, start_date, end_date, festival_income):
        empty_figure = _create_empty_figure("Пожалуйста, выберите продукт(ы)")
        empty_data = []
        empty_columns = []
        empty_conversion_text = ""

        if not product_names:
            return empty_figure, empty_data, empty_columns, empty_data, empty_columns, empty_conversion_text

        # Данные для графика и первой таблицы
        df = get_sales_by_product(product_names, start_date, end_date)
        
        # Данные для сводной таблицы
        summary_df = get_product_summary(product_names, start_date, end_date)

        if df.empty:
            return _create_empty_figure("Нет данных по выбранным продуктам за этот период"), empty_data, empty_columns, empty_data, empty_columns, empty_conversion_text

        # Округляем числовые значения до 2 знаков после запятой
        df['daily_sales'] = df['daily_sales'].round(2)
        df['cumulative_sales'] = df['cumulative_sales'].round(2)

        # Расчет процентов от дохода фестиваля
        if festival_income and festival_income > 0:
            df['cumulative_percentage'] = ((df['cumulative_sales'] / festival_income) * 100).round(2).astype(str) + '%'
            df['daily_percentage'] = ((df['daily_sales'] / festival_income) * 100).round(2).astype(str) + '%'
        else:
            df['cumulative_percentage'] = 'N/A'
            df['daily_percentage'] = 'N/A'

        # Подготовка данных для таблицы
        table_columns = [
            {"name": "Дата", "id": "date"},
            {"name": "Заявки", "id": "total_orders"},
            {"name": "Оплаты", "id": "paid_orders"},
            {"name": "Дневной доход", "id": "daily_sales"},
            {"name": "Накопительный доход", "id": "cumulative_sales"},
            {"name": "% от прихода (накоп.)", "id": "cumulative_percentage"},
            {"name": "% от прихода (дневн.)", "id": "daily_percentage"}
        ]
        table_data = df.to_dict('records')

        # Создаем фигуру с двумя осями Y
        fig = go.Figure()

        # Добавляем столбчатую диаграмму для дневного дохода (основная ось Y)
        fig.add_trace(go.Bar(
            x=df['date'],
            y=df['daily_sales'],
            name='Дневной доход',
            marker_color='blue'
        ))

        # Добавляем линейный график для накопительного дохода (вторичная ось Y)
        fig.add_trace(go.Scatter(
            x=df['date'],
            y=df['cumulative_sales'],
            name='Накопительный доход',
            yaxis='y2',
            mode='lines+markers',
            line=dict(color='red')
        ))

        # Настраиваем layout
        title_text = "Динамика дохода по выбранным продуктам"
        if len(product_names) == 1:
            title_text = f'Динамика дохода по продукту: {product_names[0]}'
        elif len(product_names) > 1:
            title_text = f'Динамика дохода по продуктам: {", ".join(product_names)}'

        fig.update_layout(
            title=title_text,
            xaxis_title='Дата',
            yaxis=dict(
                title='Дневной доход',
                titlefont=dict(color='blue'),
                tickfont=dict(color='blue')
            ),
            yaxis2=dict(
                title='Накопительный доход',
                titlefont=dict(color='red'),
                tickfont=dict(color='red'),
                overlaying='y',
                side='right'
            ),
            legend=dict(x=0.1, y=1.1, orientation='h'),
            margin=dict(l=60, r=60, t=60, b=60)
        )
        # Логика для сводной таблицы и конверсии
        if summary_df.empty:
            summary_table_data = []
            summary_table_columns = []
            conversion_text = ""
        else:
            # Расчет итоговой строки
            total_orders = summary_df['total_orders'].sum()
            paid_orders = summary_df['paid_orders'].sum()
            total_income = summary_df['total_income'].sum()
            overall_avg_check = (total_income / paid_orders) if paid_orders > 0 else 0

            # Расчет конверсии
            conversion_rate = (paid_orders / total_orders * 100) if total_orders > 0 else 0
            conversion_text = [
                html.B("Конверсия заявок в оплату: "),
                f"Всего заявок: {total_orders}, ",
                f"Всего оплаченных заявок: {paid_orders}, ",
                f"Конверсия: {conversion_rate:.2f}%"
            ]

            # Форматирование
            summary_df['total_income'] = summary_df['total_income'].round(2)
            summary_df['average_check'] = summary_df['average_check'].fillna(0).round(2)

            total_row = {
                'product': 'Итого',
                'total_orders': total_orders,
                'paid_orders': paid_orders,
                'total_income': round(total_income, 2),
                'average_check': round(overall_avg_check, 2)
            }
            
            summary_table_data = summary_df.to_dict('records')
            summary_table_data.append(total_row)

            summary_table_columns = [
                {"name": "Продукт", "id": "product"},
                {"name": "Заявки", "id": "total_orders"},
                {"name": "Оплаты", "id": "paid_orders"},
                {"name": "Доход", "id": "total_income"},
                {"name": "Средний чек", "id": "average_check"},
            ]

        return fig, table_data, table_columns, summary_table_data, summary_table_columns, conversion_text

def _create_empty_figure(text):
    """Создает пустую фигуру с текстовым сообщением."""
    return {
        "layout": {
            "xaxis": {"visible": False},
            "yaxis": {"visible": False},
            "annotations": [{
                "text": text,
                "xref": "paper",
                "yref": "paper",
                "showarrow": False,
                "font": {"size": 16}
            }]
        }
    }

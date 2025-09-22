"""
Callbacks для Dash-приложения.
Здесь определяется интерактивная логика дашборда.
"""
from datetime import datetime, timedelta
from dash import html, dcc
from dash.dependencies import Input, Output, State, ClientsideFunction
from dash.exceptions import PreventUpdate
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from .queries import (
    get_sales_by_day, get_unique_products, get_sales_by_product, 
    get_product_summary, get_paid_products_summary, get_categories,
    get_category_revenue_by_period
)
from analytics.models import SessionLocal
from partner_analytics import queries as partner_queries

def register_callbacks(app):
    """
    Регистрирует все callbacks для Dash-приложения.
    """
    # Callback для обновления графика на первой вкладке (Общая динамика)
    @app.callback(
        Output('sales-by-day-chart', 'figure'),
        [Input('start-date-picker-general', 'date'),
         Input('end-date-picker-general', 'date'),
         Input('category-dropdown-general', 'value')]
    )
    def update_general_sales_chart(start_date, end_date, category_id):
        if not start_date or not end_date:
            raise PreventUpdate
        
        # Корректируем конечную дату, чтобы включить весь день
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_corrected = end_date_dt.strftime('%Y-%m-%d')

        df = get_sales_by_day(start_date, end_date_corrected, category_id)
        if df.empty:
            return _create_empty_figure("Нет данных за выбранный период")
            
        fig = px.line(
            df, x='date', y='total_sales', title='Динамика дохода по дням',
            labels={'date': 'Дата', 'total_sales': 'Сумма дохода'}
        )
        fig.update_layout(margin=dict(l=40, r=40, t=40, b=40))
        return fig

    # Callback для загрузки списка категорий во все дропдауны
    @app.callback(
        [Output('category-dropdown-general', 'options'),
         Output('category-dropdown-product', 'options'),
         Output('category-dropdown-period', 'options'),
         Output('exclude-category-dropdown', 'options')],
        [Input('tabs-main', 'value')] # Триггер при загрузке любой вкладки
    )
    def update_category_dropdowns(tab):
        categories = get_categories()
        return [categories, categories, categories, categories]

    # Callback для обновления списка продуктов в зависимости от выбранной категории
    @app.callback(
        Output('product-dropdown', 'options'),
        [Input('category-dropdown-product', 'value')]
    )
    def update_product_dropdown(category_id):
        products = get_unique_products(category_id)
        return [{'label': i, 'value': i} for i in products]

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
         Input('end-date-picker-product', 'date'),
         Input('category-dropdown-product', 'value')],
        [State('festival-income-input', 'value')]
    )
    def update_product_sales_chart(product_names, start_date, end_date, category_id, festival_income):
        if product_names is None:
            product_names = []
            
        if not all([start_date, end_date]):
            raise PreventUpdate

        # Корректируем конечную дату
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_corrected = end_date_dt.strftime('%Y-%m-%d')

        empty_figure = _create_empty_figure("Пожалуйста, выберите продукт(ы)")
        empty_data = []
        empty_columns = []
        empty_conversion_text = ""

        if not product_names and not category_id:
            return empty_figure, empty_data, empty_columns, empty_data, empty_columns, empty_conversion_text

        # Данные для графика и первой таблицы
        df = get_sales_by_product(product_names, start_date, end_date_corrected, category_id)
        
        # Данные для сводной таблицы
        summary_df = get_product_summary(product_names, start_date, end_date_corrected, category_id)

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

        # Расчет дневной конверсии
        df['daily_conversion'] = '0.00%'
        mask = df['total_orders'] > 0
        df.loc[mask, 'daily_conversion'] = ((df.loc[mask, 'paid_orders'] / df.loc[mask, 'total_orders']) * 100).round(2).astype(str) + '%'

        # Подготовка данных для таблицы
        table_columns = [
            {"name": "Дата", "id": "date"},
            {"name": "Заявки", "id": "total_orders"},
            {"name": "Оплаты", "id": "paid_orders"},
            {"name": "Конверсия", "id": "daily_conversion"},
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

    # Callback для обновления отчета "Период и продажи"
    @app.callback(
        [Output('period-sales-table', 'data'),
         Output('period-sales-table', 'columns')],
        [Input('period-sales-date-picker', 'start_date'),
         Input('period-sales-date-picker', 'end_date'),
         Input('category-dropdown-period', 'value')]
    )
    def update_period_sales_report(start_date, end_date, category_id):
        if not start_date or not end_date:
            raise PreventUpdate

        # Корректируем конечную дату
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_corrected = end_date_dt.strftime('%Y-%m-%d')

        df = get_paid_products_summary(start_date, end_date_corrected, category_id)

        # Подготовка колонок для таблицы
        table_columns = [
            {"name": "Продукт", "id": "product"},
            {"name": "Заявки", "id": "total_orders"},
            {"name": "Оплаты", "id": "paid_orders"},
            {"name": "Конверсия", "id": "conversion"},
            {"name": "Доход", "id": "total_income"},
        ]

        if df.empty:
            return [], table_columns

        # Расчет конверсии для каждой строки
        df['conversion'] = '0.00%'
        mask = df['total_orders'] > 0
        df.loc[mask, 'conversion'] = ((df.loc[mask, 'paid_orders'] / df.loc[mask, 'total_orders']) * 100).round(2).astype(str) + '%'
        
        # Округление дохода
        df['total_income'] = df['total_income'].round(2)

        # Расчет итоговой строки
        total_orders = df['total_orders'].sum()
        total_paid_orders = df['paid_orders'].sum()
        total_income = df['total_income'].sum()
        
        # Расчет общей конверсии
        overall_conversion_rate = (total_paid_orders / total_orders * 100) if total_orders > 0 else 0
        overall_conversion_str = f"{overall_conversion_rate:.2f}%"

        total_row = {
            'product': 'Итого',
            'total_orders': total_orders,
            'paid_orders': total_paid_orders,
            'conversion': overall_conversion_str,
            'total_income': round(total_income, 2)
        }
        
        table_data = df.to_dict('records')
        table_data.append(total_row)

        return table_data, table_columns

    # Callback для обновления вкладки "Анализ дохода по категориям"
    @app.callback(
        [Output('category-revenue-bar-chart', 'figure'),
         Output('category-revenue-pie-chart', 'figure'),
         Output('category-revenue-table', 'data'),
         Output('category-revenue-table', 'columns')],
        [Input('category-revenue-date-picker', 'start_date'),
         Input('category-revenue-date-picker', 'end_date'),
         Input('exclude-category-dropdown', 'value')]
    )
    def update_category_revenue_tab(start_date, end_date, excluded_categories):
        if not start_date or not end_date:
            raise PreventUpdate

        # Корректируем конечную дату
        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_corrected = end_date_dt.strftime('%Y-%m-%d')

        df = get_category_revenue_by_period(start_date, end_date_corrected, excluded_categories)

        empty_figure = _create_empty_figure("Нет данных за выбранный период")
        
        if df.empty:
            return empty_figure, empty_figure, [], []

        # 1. Столбчатый график
        bar_fig = px.bar(
            df, 
            x='category_name', 
            y='total_revenue',
            title='Доход по категориям',
            labels={'category_name': 'Категория', 'total_revenue': 'Суммарный доход'},
            text='total_revenue'
        )
        bar_fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
        bar_fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        # 2. Круговой график
        pie_fig = px.pie(
            df, 
            names='category_name', 
            values='total_revenue',
            title='Доля категорий в общем доходе',
            hole=.3
        )
        pie_fig.update_traces(textposition='inside', textinfo='percent+label')

        # 3. Таблица
        df['total_revenue'] = df['total_revenue'].round(2)
        table_data = df.to_dict('records')
        table_columns = [
            {"name": "Категория", "id": "category_name"},
            {"name": "Доход", "id": "total_revenue"},
        ]

        return bar_fig, pie_fig, table_data, table_columns

    # Callback для обновления вкладки "Аналитика по партнерам"
    @app.callback(
        [Output('partner-analytics-chart', 'figure'),
         Output('partner-analytics-income-chart', 'figure'),
         Output('partner-analytics-table', 'data'),
         Output('partner-analytics-table', 'columns')],
        [Input('partner-analytics-date-picker', 'start_date'),
         Input('partner-analytics-date-picker', 'end_date'),
         Input('exclude-common-source-checklist', 'value'),
         Input('show-income-checklist', 'value')]
    )
    def update_partner_analytics_tab(start_date, end_date, exclude_common_value, show_income_value):
        if not start_date or not end_date:
            raise PreventUpdate

        exclude_common = 'exclude' in exclude_common_value
        show_income = 'show' in show_income_value

        db = SessionLocal()
        try:
            data = partner_queries.get_partner_analytics_data(db, start_date, end_date, exclude_common)
        finally:
            db.close()

        empty_fig = _create_empty_figure("")
        if not data:
            return _create_empty_figure("Нет данных за выбранный период"), empty_fig, [], []

        df = pd.DataFrame(data, columns=['partner', 'order_count', 'total_income'])

        # Сортируем данные для графика по регистрациям
        df_sorted_by_registrations = df.sort_values(by='order_count', ascending=False)

        # График по регистрациям
        registrations_fig = px.bar(
            df_sorted_by_registrations,
            x='partner',
            y='order_count',
            title='Количество регистраций по партнерам',
            labels={'partner': 'Партнер', 'order_count': 'Количество регистраций'},
            text='order_count'
        )
        registrations_fig.update_traces(textposition='outside')
        registrations_fig.update_layout(
            uniformtext_minsize=8, 
            uniformtext_mode='hide',
            yaxis_range=[0, df_sorted_by_registrations['order_count'].max() * 1.1] # Увеличиваем диапазон оси Y
        )

        # График по доходу (если нужно)
        income_fig = empty_fig
        if show_income:
            income_fig = px.bar(
                df,
                x='partner',
                y='total_income',
                title='Доход по партнерам',
                labels={'partner': 'Партнер', 'total_income': 'Доход'},
                text='total_income'
            )
            income_fig.update_traces(texttemplate='%{text:.2s}', textposition='outside')
            income_fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')

        # Таблица
        df['total_income'] = df['total_income'].round(2)
        table_data = df.to_dict('records')
        
        table_columns = [
            {"name": "Партнер", "id": "partner"},
            {"name": "Количество регистраций", "id": "order_count"},
        ]
        if show_income:
            table_columns.append({"name": "Доход", "id": "total_income"})

        return registrations_fig, income_fig, table_data, table_columns

    # Clientside callback для экспорта в PDF
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='print_page'
        ),
        Output('export-pdf-button', 'children'),
        [Input('export-pdf-button', 'n_clicks')]
    )

    # Callback для экспорта в Excel
    @app.callback(
        Output("download-excel", "data"),
        [Input("export-excel-button", "n_clicks")],
        [State("partner-analytics-table", "data")]
    )
    def download_excel(n_clicks, data):
        if n_clicks == 0 or not data:
            raise PreventUpdate
        
        df = pd.DataFrame(data)
        return dcc.send_data_frame(df.to_excel, "partner_analytics.xlsx", sheet_name="Sheet_1", index=False)

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

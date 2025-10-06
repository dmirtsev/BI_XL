"""
Callbacks для Dash-приложения.
Здесь определяется интерактивная логика дашборда.
"""
import pytz
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
    get_category_revenue_by_period, get_monthly_sales, get_monthly_sales_by_product,
    get_monthly_sales_by_category
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
         Output('exclude-category-dropdown', 'options'),
         Output('include-category-dropdown', 'options'),
         Output('monthly-sales-category-dropdown', 'options')],
        [Input('tabs-main', 'value')] # Триггер при загрузке любой вкладки
    )
    def update_category_dropdowns(tab):
        categories = get_categories()
        return [categories, categories, categories, categories, categories, categories]

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
         Output('conversion-summary-div', 'children'),
         Output('max-date-store', 'data')],  # Добавляем вывод в хранилище
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
        empty_max_date = None

        if not product_names and not category_id:
            return empty_figure, empty_data, empty_columns, empty_data, empty_columns, empty_conversion_text, empty_max_date

        # Данные для графика и первой таблицы
        df, max_creation_date = get_sales_by_product(product_names, start_date, end_date_corrected, category_id)
        
        # Данные для сводной таблицы
        summary_df = get_product_summary(product_names, start_date, end_date_corrected, category_id)

        if df.empty:
            return _create_empty_figure("Нет данных по выбранным продуктам за этот период"), empty_data, empty_columns, empty_data, empty_columns, empty_conversion_text, empty_max_date

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

            conversion_text = []

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
                {"name": "Оплаты", "id": "paid_orders"},
                {"name": "Доход", "id": "total_income"},
                {"name": "Средний чек", "id": "average_check"},
            ]

        # Преобразуем дату в строку для JSON-сериализации
        max_date_str = max_creation_date.isoformat() if max_creation_date else None
        return fig, table_data, table_columns, summary_table_data, summary_table_columns, conversion_text, max_date_str

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
            {"name": "Оплаты", "id": "paid_orders"},
            {"name": "Доход", "id": "total_income"},
        ]

        if df.empty:
            return [], table_columns

        # Округление дохода
        df['total_income'] = df['total_income'].round(2)

        # Расчет итоговой строки
        total_paid_orders = df['paid_orders'].sum()
        total_income = df['total_income'].sum()

        total_row = {
            'product': 'Итого',
            'paid_orders': total_paid_orders,
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
         Input('exclude-category-dropdown', 'value'),
         Input('include-category-dropdown', 'value'),
         Input('category-revenue-date-checklist', 'value')]
    )
    def update_category_revenue_tab(start_date, end_date, excluded_categories, included_categories, date_checklist):
        use_dates = 'USE_DATES' in date_checklist

        if use_dates and (not start_date or not end_date):
            raise PreventUpdate

        start_date_final = None
        end_date_final = None
        if use_dates:
            # Корректируем конечную дату
            end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            end_date_final = end_date_dt.strftime('%Y-%m-%d')
            start_date_final = start_date

        df = get_category_revenue_by_period(start_date_final, end_date_final, excluded_categories, included_categories)

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
        total_revenue_sum = df['total_revenue'].sum()
        df['total_revenue'] = df['total_revenue'].round(2)
        table_data = df.to_dict('records')
        
        # Добавляем итоговую строку
        table_data.append({
            'category_name': 'Итого',
            'total_revenue': round(total_revenue_sum, 2)
        })

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

        df = pd.DataFrame(data, columns=['partner', 'utm_source', 'order_count', 'total_income'])

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
            {"name": "UTM Source", "id": "utm_source"},
            {"name": "Количество регистраций", "id": "order_count"},
        ]
        if show_income:
            table_columns.append({"name": "Доход", "id": "total_income"})

        return registrations_fig, income_fig, table_data, table_columns

    # Clientside callback для экспорта в PDF (закомментировано из-за ошибки)
    # app.clientside_callback(
    #     ClientsideFunction(
    #         namespace='clientside',
    #         function_name='print_page'
    #     ),
    #     Output('export-pdf-button', 'children'),
    #     [Input('export-pdf-button', 'n_clicks')]
    # )

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

    # Callback для обновления общего дохода и блока "Бирюзовый фонд"
    @app.callback(
        [Output('total-income-product', 'children'),
         Output('turquoise-fund-block', 'style'),
         Output('turquoise-fund-title', 'children'),
         Output('turquoise-fund-income', 'children'),
         Output('turquoise-fund-after-tax', 'children'),
         Output('employee-income', 'children')],
        [Input('product-summary-table', 'data'),
         Input('category-dropdown-product', 'value'),
         Input('employee-count-input', 'value'),
         Input('max-date-store', 'data')],
        [State('category-dropdown-product', 'options')]
    )
    def update_turquoise_fund(summary_data, category_id, employee_count, max_date_str, category_options):
        default_title = "Бирюзовый фонд"
        if not summary_data:
            return "Общий доход: 0.00 руб.", {'display': 'none'}, default_title, "", "", ""

        # 1. Расчет общего дохода
        total_income = 0
        # Итоговая строка обычно последняя
        if summary_data and summary_data[-1]['product'] == 'Итого':
            total_income = summary_data[-1].get('total_income', 0)
        
        total_income_text = f"Общий доход: {total_income:,.2f} руб.".replace(',', ' ')

        # 2. Логика для "Бирюзового фонда"
        show_turquoise_block = False
        category_name = ""
        if category_id and category_options:
            # Находим полное имя категории
            for option in category_options:
                if option['value'] == category_id:
                    category_name = option['label']
                    break
        
        if "АстроФест" in category_name:
            show_turquoise_block = True

        if not show_turquoise_block:
            return total_income_text, {'display': 'none'}, default_title, "", "", ""

        # Формируем заголовок с датой
        title = default_title
        if max_date_str:
            # Конвертируем время в московское
            utc_date = datetime.fromisoformat(max_date_str).replace(tzinfo=pytz.utc)
            moscow_tz = pytz.timezone('Europe/Moscow')
            moscow_date = utc_date.astimezone(moscow_tz)
            title += f" на {moscow_date.strftime('%d.%m.%Y %H:%M')}"

        # Расчеты для фонда
        fund_income = total_income * 0.20
        fund_after_tax = fund_income * 0.94  # Вычет 6%
        
        employee_income = 0
        if employee_count and employee_count > 0:
            employee_income = fund_after_tax / employee_count

        # Стили
        text_style = {'fontWeight': 'bold', 'color': '#008080'} # Темно-бирюзовый
        number_style = {'fontSize': '1.2em', 'color': 'purple', 'fontWeight': 'bold', 'marginLeft': '5px'}

        # Формирование стилизованных выводов
        fund_income_text = html.Div([
            html.Span("Бирюзовый фонд (доход): ", style=text_style),
            html.Span(f"{fund_income:,.2f} руб.".replace(',', ' '), style=number_style)
        ])
        fund_after_tax_text = html.Div([
            html.Span("Бирюзовый фонд (с вычетом 6%): ", style=text_style),
            html.Span(f"{fund_after_tax:,.2f} руб.".replace(',', ' '), style=number_style)
        ])
        employee_income_text = html.Div([
            html.Span("Доход сотрудника: ", style=text_style),
            html.Span(f"{employee_income:,.2f} руб.".replace(',', ' '), style=number_style)
        ])
        
        style = {'display': 'block', 'marginTop': '30px', 'padding': '15px', 'border': '2px solid #40E0D0', 'borderRadius': '5px'}

        return total_income_text, style, title, fund_income_text, fund_after_tax_text, employee_income_text


    # Callback для обновления списка продуктов на вкладке "Помесячные продажи"
    @app.callback(
        Output('monthly-sales-product-dropdown', 'options'),
        [Input('monthly-sales-category-dropdown', 'value')]
    )
    def update_monthly_sales_product_dropdown(category_ids):
        if not category_ids:
            # Если категории не выбраны, можно вернуть пустой список или все продукты
            products = get_unique_products()
        else:
            products = get_unique_products(category_id=category_ids)
        return [{'label': i, 'value': i} for i in products]

    # Callback для обновления вкладки "Помесячные продажи"
    @app.callback(
        [Output('monthly-sales-graph', 'figure'),
         Output('monthly-sales-table', 'data'),
         Output('monthly-sales-table', 'columns'),
         Output('monthly-sales-summary', 'children'),
         Output('monthly-sales-by-product-graph', 'figure'),
         Output('monthly-sales-by-product-table', 'data'),
         Output('monthly-sales-by-product-table', 'columns'),
         Output('monthly-sales-by-product-summary', 'children'),
         Output('monthly-sales-by-category-graph', 'figure'),
         Output('monthly-sales-by-category-table', 'data'),
         Output('monthly-sales-by-category-table', 'columns'),
         Output('monthly-sales-by-category-summary', 'children')],
        [Input('monthly-sales-date-picker', 'start_date'),
         Input('monthly-sales-date-picker', 'end_date'),
         Input('monthly-sales-category-dropdown', 'value'),
         Input('monthly-sales-product-dropdown', 'value')]
    )
    def update_monthly_sales_tab(start_date, end_date, category_ids, product_names):
        if not start_date or not end_date:
            raise PreventUpdate

        end_date_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
        end_date_corrected = end_date_dt.strftime('%Y-%m-%d')

        # Получение данных
        df_monthly = get_monthly_sales(start_date, end_date_corrected, category_ids, product_names)
        df_by_product = get_monthly_sales_by_product(start_date, end_date_corrected, category_ids, product_names)
        df_by_category = get_monthly_sales_by_category(start_date, end_date_corrected, category_ids, product_names)

        empty_fig = _create_empty_figure("Нет данных за выбранный период")
        empty_summary = []
        if df_monthly.empty:
            return empty_fig, [], [], empty_summary, empty_fig, [], [], empty_summary, empty_fig, [], [], empty_summary

        # --- Общая функция для создания сводки ---
        def create_summary(df, total_sales_col='total_sales', total_orders_col='total_orders', paid_orders_col='paid_orders', is_monthly=False):
            total_sales = df[total_sales_col].sum()
            paid_orders = df[paid_orders_col].sum()
            average_check = (total_sales / paid_orders) if paid_orders > 0 else 0
            
            summary_items = [
                html.B("Сводка: "),
                f"Итоговый доход: {total_sales:,.2f} руб., ".replace(",", " "),
                f"Всего оплат: {paid_orders}, ",
                f"Средний чек: {average_check:,.2f} руб.".replace(",", " ")
            ]

            if is_monthly and not df.empty:
                num_months = df['month'].nunique()
                average_monthly_income = (total_sales / num_months) if num_months > 0 else 0
                summary_items.append(f"Средний доход в месяц: {average_monthly_income:,.2f} руб.".replace(",", " "))

            return summary_items

        # --- Первый график, таблица и сводка (общие) ---
        total_monthly_sales = df_monthly['total_sales'].sum()
        total_monthly_orders = df_monthly['total_orders'].sum()
        total_monthly_paid_orders = df_monthly['paid_orders'].sum()
        
        fig_monthly = px.bar(
            df_monthly, x='month', y='total_sales', title='Динамика продаж по месяцам',
            labels={'month': 'Месяц', 'total_sales': 'Сумма продаж'}, text='total_sales'
        )
        fig_monthly.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig_monthly.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title="Сумма продаж")
        
        summary_monthly = create_summary(df_monthly, 'total_sales', 'total_orders', 'paid_orders', is_monthly=True)
        df_monthly['total_sales'] = df_monthly['total_sales'].apply(lambda x: f"{x:,.2f}".replace(",", " "))
        table_monthly_data = df_monthly.to_dict('records')
        table_monthly_data.append({
            'month': 'Итого',
            'total_sales': f"{total_monthly_sales:,.2f}".replace(",", " "),
            'paid_orders': total_monthly_paid_orders
        })
        table_monthly_columns = [
            {"name": "Месяц", "id": "month"}, {"name": "Сумма продаж", "id": "total_sales"},
            {"name": "Оплаты", "id": "paid_orders"}
        ]

        # --- Второй график, таблица и сводка (по продуктам) ---
        if df_by_product.empty:
            fig_by_product, table_by_product_data, table_by_product_columns, summary_by_product = empty_fig, [], [], empty_summary
        else:
            total_product_sales = df_by_product['total_sales'].sum()
            total_product_orders = df_by_product['total_orders'].sum()
            total_product_paid_orders = df_by_product['paid_orders'].sum()

            fig_by_product = px.bar(
                df_by_product, x='month', y='total_sales', color='product', title='Динамика продаж по продуктам',
                labels={'month': 'Месяц', 'total_sales': 'Сумма продаж', 'product': 'Продукт'},
                barmode='group', text='total_sales'
            )
            fig_by_product.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_by_product.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title="Сумма продаж")
            
            summary_by_product = create_summary(df_by_product, 'total_sales', 'total_orders', 'paid_orders', is_monthly=True)
            df_by_product['total_sales'] = df_by_product['total_sales'].apply(lambda x: f"{x:,.2f}".replace(",", " "))
            table_by_product_data = df_by_product.to_dict('records')
            table_by_product_data.append({
                'month': 'Итого',
                'product': '',
                'total_sales': f"{total_product_sales:,.2f}".replace(",", " "),
                'paid_orders': total_product_paid_orders
            })
            table_by_product_columns = [
                {"name": "Месяц", "id": "month"}, {"name": "Продукт", "id": "product"},
                {"name": "Сумма продаж", "id": "total_sales"},
                {"name": "Оплаты", "id": "paid_orders"}
            ]

        # --- Третий график, таблица и сводка (по категориям) ---
        if df_by_category.empty:
            fig_by_category, table_by_category_data, table_by_category_columns, summary_by_category = empty_fig, [], [], empty_summary
        else:
            total_category_sales = df_by_category['total_sales'].sum()
            total_category_orders = df_by_category['total_orders'].sum()
            total_category_paid_orders = df_by_category['paid_orders'].sum()

            fig_by_category = px.bar(
                df_by_category, x='month', y='total_sales', color='category', title='Динамика продаж по категориям',
                labels={'month': 'Месяц', 'total_sales': 'Сумма продаж', 'category': 'Категория'},
                barmode='group', text='total_sales'
            )
            fig_by_category.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig_by_category.update_layout(uniformtext_minsize=8, uniformtext_mode='hide', yaxis_title="Сумма продаж")
            
            summary_by_category = create_summary(df_by_category, 'total_sales', 'total_orders', 'paid_orders', is_monthly=True)
            df_by_category['total_sales'] = df_by_category['total_sales'].apply(lambda x: f"{x:,.2f}".replace(",", " "))
            table_by_category_data = df_by_category.to_dict('records')
            table_by_category_data.append({
                'month': 'Итого',
                'category': '',
                'total_sales': f"{total_category_sales:,.2f}".replace(",", " "),
                'paid_orders': total_category_paid_orders
            })
            table_by_category_columns = [
                {"name": "Месяц", "id": "month"}, {"name": "Категория", "id": "category"},
                {"name": "Сумма продаж", "id": "total_sales"},
                {"name": "Оплаты", "id": "paid_orders"}
            ]

        return (fig_monthly, table_monthly_data, table_monthly_columns, summary_monthly,
                fig_by_product, table_by_product_data, table_by_product_columns, summary_by_product,
                fig_by_category, table_by_category_data, table_by_category_columns, summary_by_category)

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

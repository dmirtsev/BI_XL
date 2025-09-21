"""
Определение внешнего вида (layout) Dash-приложения.
"""
from dash import dcc, html, dash_table
from datetime import date, timedelta

# Определяем layout приложения
layout = html.Div([
    html.H1("Аналитический дашборд"),
    
    dcc.Tabs(id="tabs-main", value='tab-general', children=[
        # Вкладка 1: Общая динамика
        dcc.Tab(label='Общая динамика', value='tab-general', children=[
            html.Div([
                html.Label("Выберите период:"),
                dcc.DatePickerSingle(
                    id='start-date-picker-general',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    date=date.today() - timedelta(days=30),
                    display_format='YYYY-MM-DD'
                ),
                dcc.DatePickerSingle(
                    id='end-date-picker-general',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=date.today(),
                    initial_visible_month=date.today(),
                    date=date.today(),
                    display_format='YYYY-MM-DD'
                ),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            dcc.Graph(id='sales-by-day-chart')
        ]),
        
        # Вкладка 2: Отчет по продуктам
        dcc.Tab(label='Отчет по продуктам', value='tab-product', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите продукт(ы):"),
                    dcc.Dropdown(id='product-dropdown', placeholder="Загрузка...", multi=True),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                html.Div([
                    html.Label("Приход от одного из предыдущих фестивалей (по умолчанию от Infinitum 10)"),
                    dcc.Input(
                        id='festival-income-input',
                        type='number',
                        value=722556.74,
                        style={'width': '100%', 'padding': '5px'}
                    ),
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '2%', 'verticalAlign': 'top'}),

                html.Div([
                    html.Label("Выберите период:"),
                    dcc.DatePickerSingle(
                        id='start-date-picker-product',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=date.today(),
                        initial_visible_month=date.today(),
                        date=date.today() - timedelta(days=30),
                        display_format='YYYY-MM-DD'
                    ),
                    dcc.DatePickerSingle(
                        id='end-date-picker-product',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=date.today(),
                        initial_visible_month=date.today(),
                        date=date.today(),
                        display_format='YYYY-MM-DD'
                    ),
                ], style={'width': '35%', 'display': 'inline-block', 'float': 'right', 'verticalAlign': 'top'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            dcc.Graph(id='sales-by-product-chart'),
            html.H4("Данные по доходам"),
            dash_table.DataTable(
                id='product-sales-table',
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
            ),
            html.Div(id='conversion-summary-div', style={
                'marginTop': '20px',
                'padding': '10px',
                'border': '1px solid #ddd',
                'borderRadius': '5px',
                'backgroundColor': '#f9f9f9'
            }),
            html.H4("Сводка по продуктам", style={'marginTop': '20px'}),
            dash_table.DataTable(
                id='product-summary-table',
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
            )
        ]),
        
        # Вкладка 3: Период и продажи
        dcc.Tab(label='Период и продажи', value='tab-period-sales', children=[
            html.Div([
                html.Label("Выберите период:"),
                dcc.DatePickerRange(
                    id='period-sales-date-picker',
                    min_date_allowed=date(2020, 1, 1),
                    max_date_allowed=date.today(),
                    start_date=date.today() - timedelta(days=30),
                    end_date=date.today(),
                    display_format='YYYY-MM-DD'
                ),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            
            html.Div(id='period-sales-summary-div', style={
                'marginTop': '20px',
                'padding': '10px',
                'border': '1px solid #ddd',
                'borderRadius': '5px',
                'backgroundColor': '#f9f9f9',
                'marginBottom': '20px'
            }),
            
            html.H4("Продукты с оплатой за период"),
            dash_table.DataTable(
                id='period-sales-table',
                style_cell={'textAlign': 'left'},
                style_header={
                    'backgroundColor': 'rgb(230, 230, 230)',
                    'fontWeight': 'bold'
                },
                style_data_conditional=[
                    {
                        'if': {'row_index': 'odd'},
                        'backgroundColor': 'rgb(248, 248, 248)'
                    }
                ],
            )
        ]),
    ]),
])

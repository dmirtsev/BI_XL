"""
Определение внешнего вида (layout) Dash-приложения.
"""
from dash import dcc, html, dash_table
from datetime import date, timedelta

# Определяем layout приложения
layout = html.Div([
    html.Div([
        html.H1("Аналитический дашборд", style={'display': 'inline-block', 'marginRight': '20px'}),
        html.A(html.Button("Вернуться на главный экран"), href='/', style={'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '20px'}),
    ]),
    
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
                html.Div([
                    html.Label("Выберите категорию:"),
                    dcc.Dropdown(id='category-dropdown-general', placeholder="Все категории", clearable=True),
                ], style={'width': '30%', 'display': 'inline-block', 'marginLeft': '20px'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            dcc.Graph(id='sales-by-day-chart')
        ]),
        
        # Вкладка 2: Отчет по продуктам
        dcc.Tab(label='Отчет по продуктам', value='tab-product', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите категорию:"),
                    dcc.Dropdown(id='category-dropdown-product', placeholder="Все категории", clearable=True),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),

                html.Div([
                    html.Label("Выберите продукт(ы):"),
                    dcc.Dropdown(id='product-dropdown', placeholder="Выберите категорию...", multi=True),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top', 'marginLeft': '2%'}),

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
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
            ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'flexWrap': 'wrap', 'marginTop': '20px', 'marginBottom': '20px'}),
            
            # Контейнер для общего дохода
            html.Div(id='total-income-product', style={'fontSize': 20, 'fontWeight': 'bold', 'marginTop': '20px', 'marginBottom': '20px'}),

            dcc.Graph(id='sales-by-product-chart'),
            html.H4("Данные по доходам"),
            dash_table.DataTable(
                id='product-sales-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
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
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
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
            
            # Блок для Бирюзового фонда
            html.Div(id='turquoise-fund-block', style={'display': 'none', 'marginTop': '30px', 'padding': '15px', 'border': '2px solid #40E0D0', 'borderRadius': '5px'}, children=[
                html.H4(id='turquoise-fund-title', style={'color': '#40E0D0'}),
                html.Div(id='turquoise-fund-income', style={'fontWeight': 'bold'}),
                html.Div([
                    html.Label("Число сотрудников:", style={'marginRight': '10px'}),
                    dcc.Input(id='employee-count-input', type='number', value=2, style={'width': '100px'}),
                ], style={'marginTop': '10px'}),
                html.Div(id='turquoise-fund-after-tax', style={'marginTop': '10px'}),
                html.Div(id='employee-income', style={'marginTop': '10px'}),
            ])
        ]),
        
        # Вкладка 3: Период и продажи
        dcc.Tab(label='Период и продажи', value='tab-period-sales', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите категорию:"),
                    dcc.Dropdown(id='category-dropdown-period', placeholder="Все категории", clearable=True),
                ], style={'width': '30%', 'display': 'inline-block', 'verticalAlign': 'top'}),
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
                ], style={'display': 'inline-block', 'marginLeft': '20px'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            
            html.H4("Продукты с оплатой за период"),
            dash_table.DataTable(
                id='period-sales-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '100px', 'width': '100px', 'maxWidth': '100px'},
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
        
        # Вкладка 4: Анализ дохода по категориям
        dcc.Tab(label='Анализ дохода по категориям', value='tab-category-revenue', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите период:"),
                    dcc.DatePickerRange(
                        id='category-revenue-date-picker',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=date.today(),
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today(),
                        display_format='YYYY-MM-DD'
                    ),
                    dcc.Checklist(
                        id='category-revenue-date-checklist',
                        options=[{'label': 'Учитывать даты?', 'value': 'USE_DATES'}],
                        value=['USE_DATES'], # По умолчанию включен
                        style={'marginTop': '5px'}
                    ),
                ], style={'display': 'inline-block', 'marginRight': '20px', 'verticalAlign': 'top'}),
                html.Div([
                    html.Label("Исключить категории:"),
                    dcc.Dropdown(
                        id='exclude-category-dropdown',
                        multi=True,
                        placeholder="Выберите категории для исключения"
                    ),
                ], style={'display': 'inline-block', 'width': '45%', 'marginRight': '2%'}),
                html.Div([
                    html.Label("Включить категории:"),
                    dcc.Dropdown(
                        id='include-category-dropdown',
                        multi=True,
                        placeholder="Выберите категории для включения"
                    ),
                ], style={'display': 'inline-block', 'width': '45%'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px', 'display': 'flex'}),
            
            html.Div([
                # Контейнер для графиков
                html.Div([
                    dcc.Graph(id='category-revenue-bar-chart'),
                ], style={'width': '50%', 'display': 'inline-block'}),
                
                html.Div([
                    dcc.Graph(id='category-revenue-pie-chart'),
                ], style={'width': '50%', 'display': 'inline-block'}),
            ]),
            
            html.H4("Таблица доходов по категориям"),
            dash_table.DataTable(
                id='category-revenue-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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
        
        # Вкладка 5: Аналитика по партнерам
        dcc.Tab(label='Аналитика по партнерам', value='tab-partner-analytics', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите период:"),
                    dcc.DatePickerRange(
                        id='partner-analytics-date-picker',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=date.today(),
                        start_date=date.today() - timedelta(days=30),
                        end_date=date.today(),
                        display_format='YYYY-MM-DD'
                    ),
                ], style={'display': 'inline-block', 'marginRight': '20px'}),
                html.Div([
                    dcc.Checklist(
                        id='exclude-common-source-checklist',
                        options=[{'label': 'Не учитывать "Общий источник"', 'value': 'exclude'}],
                        value=['exclude'] # По умолчанию включен
                    ),
                ], style={'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '25px', 'marginRight': '20px'}),
                html.Div([
                    dcc.Checklist(
                        id='show-income-checklist',
                        options=[{'label': 'Выводить график дохода и поле "Доход" в таблице', 'value': 'show'}],
                        value=[] # По умолчанию выключен
                    ),
                ], style={'display': 'inline-block', 'verticalAlign': 'top', 'marginTop': '25px'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            
            dcc.Graph(id='partner-analytics-chart'),
            dcc.Graph(id='partner-analytics-income-chart'),
            
            html.H4("Данные по партнерам"),
            html.Div([
                html.Button("Экспорт в Excel", id="export-excel-button", n_clicks=0),
            ], style={'marginBottom': '10px'}),
            dash_table.DataTable(
                id='partner-analytics-table',
                sort_action="native",
                export_format="xlsx",
                export_headers="display",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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
            dcc.Download(id="download-excel")
        ]),
        
        # Вкладка 6: Помесячные продажи
        dcc.Tab(label='Помесячные продажи', value='tab-monthly-sales', children=[
            html.Div([
                html.Div([
                    html.Label("Выберите период:"),
                    dcc.DatePickerRange(
                        id='monthly-sales-date-picker',
                        min_date_allowed=date(2020, 1, 1),
                        max_date_allowed=date.today(),
                        start_date=date.today() - timedelta(days=365),
                        end_date=date.today(),
                        display_format='YYYY-MM-DD'
                    ),
                ], style={'display': 'inline-block', 'marginRight': '20px', 'verticalAlign': 'top'}),
                html.Div([
                    html.Label("Выберите категорию:"),
                    dcc.Dropdown(
                        id='monthly-sales-category-dropdown',
                        multi=True,
                        placeholder="Все категории"
                    ),
                ], style={'display': 'inline-block', 'width': '30%', 'marginRight': '2%', 'verticalAlign': 'top'}),
                html.Div([
                    html.Label("Выберите продукт(ы):"),
                    dcc.Dropdown(
                        id='monthly-sales-product-dropdown',
                        multi=True,
                        placeholder="Все продукты"
                    ),
                ], style={'display': 'inline-block', 'width': '30%', 'verticalAlign': 'top'}),
            ], style={'marginTop': '20px', 'marginBottom': '20px'}),
            
            dcc.Graph(id='monthly-sales-graph'),
            
            html.H4("Данные по месяцам"),
            dash_table.DataTable(
                id='monthly-sales-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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

            html.Hr(style={'marginTop': '30px', 'marginBottom': '30px'}),

            html.H4("Продажи по продуктам за месяц"),
            dcc.Graph(id='monthly-sales-by-product-graph'),

            html.H4("Данные по продуктам за месяц"),
            dash_table.DataTable(
                id='monthly-sales-by-product-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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

            html.Hr(style={'marginTop': '30px', 'marginBottom': '30px'}),

            html.H4("Продажи по категориям за месяц"),
            dcc.Graph(id='monthly-sales-by-category-graph'),

            html.H4("Данные по категориям за месяц"),
            dash_table.DataTable(
                id='monthly-sales-by-category-table',
                sort_action="native",
                filter_action="native",
                style_table={'overflowX': 'auto'},
                style_cell={'textAlign': 'left', 'minWidth': '150px', 'width': '150px', 'maxWidth': '150px'},
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
    dcc.Store(id='max-date-store') # Хранилище для максимальной даты
])

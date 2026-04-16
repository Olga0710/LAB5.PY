import dash
import pandas as pd
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv('weather2026.csv')

df['хмарність_число'] = df['хмарність'].str.replace('%', '').astype(float)
df['денна_темп'] = df['денна температура повітря'].str.replace('°C', '').astype(float)
df['нічна_темп'] = df['нічна температура повітря'].str.replace('°C', '').astype(float)
df['сила_вітру_число'] = df['сила вітру'].str.replace(' м/с', '', regex=False).astype(float)
df['опади_число'] = df['опади'].replace('-', '0').str.replace(' м.м.', '', regex=False).astype(float)

df['період'] = df['період'].astype(str).str.strip()
df = df[df['період'] != 'nan']
df = df[df['період'] != '']
df = df[df['період'] != 'None']
df = df.dropna(subset=['період', 'день'])

df['Дата'] = pd.to_datetime(df['період'] + '-' + df['день'].astype(str), errors='coerce')
df = df.dropna(subset=['Дата'])

bins = [0, 35, 70, 101]
labels = ['Сонячний', 'Мінлива хмарність', 'Хмарний']
df['тип_хмарності'] = pd.cut(df['хмарність_число'], bins=bins, labels=labels, right=False)

df['розмір_бульбашки'] = df['опади_число'].replace(0, 5)
df['відхилення'] = df['нічна_темп'] - df['денна_темп']

unique_months = sorted(df['період'].unique())

app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Лабораторна робота №5", style={'textAlign': 'center'}),
    html.H5("Виконавець: Бережна Ольга, група К-27. Викладач: Карнаух Тетяна Олександрівна", 
            style={'textAlign': 'right', 'marginRight': '50px'}),
    html.Hr(),

    html.Div([
        html.Div([
            html.H3("Помісячні графіки"),
            html.Label("Оберіть місяць:"),
            dcc.Dropdown(
                id='month-selector',
                options=[{'label': m, 'value': m} for m in unique_months],
                value=unique_months[0] if unique_months else None,
                clearable=False
            ),
            html.Br(),
            html.Label("Тип графіка:"),
            dcc.RadioItems(
                id='graph-type',
                options=[
                    {'label': 'Температура (День/Ніч)', 'value': 'temp'},
                    {'label': 'Хмарність', 'value': 'cloud'},
                    {'label': 'Сила вітру', 'value': 'wind'},
                    {'label': 'Опади (бульбашковий)', 'value': 'bubble'},
                ],
                value='temp'
            )
        ], style={'width': '28%', 'display': 'inline-block', 'padding': '20px',
                  'backgroundColor': '#f0f0f0', 'borderRadius': '10px', 'verticalAlign': 'top'}),
        
        html.Div([
            dcc.Graph(id='monthly-display')
        ], style={'width': '68%', 'display': 'inline-block', 'padding': '10px'})
    ]),
    
    html.Hr(),

    html.Div([
        html.H3("Загальна аналітика", style={'textAlign': 'center'}),
        html.Div([
            html.Label("Оберіть тип аналітики:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='analytics-type',
                options=[
                    {'label': 'Гістограма відхилення температури', 'value': 'hist'},
                    {'label': 'Стовпчикова діаграма хмарності', 'value': 'bar_stacked'},
                    {'label': 'Діаграма "Сонячного вибуху"', 'value': 'sunburst'},
                    {'label': 'Кругова діаграма (опади)', 'value': 'pie'}
                ],
                value='hist',
                clearable=False
            )
        ], style={'width': '60%', 'marginBottom': '20px'}),
        
        html.Div([
            dcc.Graph(id='analytics-graph')
        ])
    ])
])

@app.callback(
    Output('monthly-display', 'figure'),
    [Input('month-selector', 'value'), Input('graph-type', 'value')]
)
def update_monthly_graph(selected_month, graph_type):
    if selected_month is None:
        return px.scatter(title="Оберіть місяць")
    
    dff = df[df['період'] == selected_month].copy()
    
    if dff.empty:
        return px.scatter(title=f"Немає даних за {selected_month}")
    
    if graph_type == 'temp':
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dff['день'], y=dff['денна_темп'],
                                 name='Денна', mode='lines+markers'))
        fig.add_trace(go.Scatter(x=dff['день'], y=dff['нічна_темп'], 
                                 name='Нічна', mode='lines+markers'))
        fig.update_layout(title=f"Температура у {selected_month}",
                          xaxis_title="День місяця", yaxis_title="Температура (°C)")
        return fig
        
    elif graph_type == 'cloud':
        fig = px.bar(dff, x='день', y='хмарність_число',
                     title=f"Хмарність за {selected_month}",
                     labels={'день': 'День', 'хмарність_число': 'Хмарність (%)'})
        return fig
        
    elif graph_type == 'wind':
        fig = px.bar(dff, x='день', y='сила_вітру_число',
                    title=f"Сила вітру (м/с) - {selected_month}",
                    labels={'сила_вітру_число': 'Швидкість вітру (м/с)'})
        return fig
        
    else:
        fig = px.scatter(dff, x='день', y='денна_темп', size='розмір_бульбашки',
                         title=f"Денна температура та опади - {selected_month}",
                         labels={'денна_темп': 'Температура (°C)', 'день': 'День місяця'},
                         size_max=25)
        return fig

@app.callback(
    Output('analytics-graph', 'figure'),
    [Input('analytics-type', 'value')]
)
def update_analytics(analytics_type):
    try:
        if analytics_type == 'hist':
            dff = df.dropna(subset=['відхилення'])
            fig = px.histogram(dff, x='відхилення', nbins=20,title="Гістограма відхилення нічної температури від денної",labels={'відхилення': 'Відхилення (Нічна - Денна) °C'})
            return fig
           
        elif analytics_type == 'bar_stacked':
            count_df = df.groupby(['період', 'тип_хмарності'], observed=True).size().reset_index(name='кількість_днів')            
            fig = px.bar(count_df, x='період', y='кількість_днів', color='тип_хмарності', title="Кількість днів за типами хмарності (з накопиченням)", labels={'період': 'Місяць', 'кількість_днів': 'Кількість днів', 'тип_хмарності': 'Тип хмарності'},barmode='stack') 
            return fig
        
        elif analytics_type == 'sunburst':
            sunburst_data = df.groupby(['період', 'тип_хмарності'], observed=True).size().reset_index(name='кількість_днів')           
            fig = px.sunburst(sunburst_data, path=['період', 'тип_хмарності'], values='кількість_днів', title="Діаграма 'Сонячного вибуху' - Розподіл типів хмарності по місяцях")
            return fig 
        elif analytics_type == 'pie':  
            rainy_days = df[df['опади_число'] >0].groupby('період').size().reset_index(name='кількість')
            fig = px.pie(rainy_days, values='кількість', names='період',title='Розподіл днів з опадами по місяцях (весь період)',hole=0.3)
            fig.update_traces(textposition='inside', textinfo='percent', textfont_size=12)
            fig.update_layout(showlegend=True, legend_title_text='Місяць')
            return fig
    
    except Exception as e:
        return px.scatter(title=f"Помилка: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
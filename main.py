import base64
import io
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
from io import StringIO

from AnalyticsAPP.DataAnalytics import *

# Inicializa o app Dash
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],)

app.title = "Fast Data Analytics"
server = app.server


app.title = "Fast Data Analytics"

server = app.server

# Layout do aplicativo
app.layout = html.Div([
    html.Div([
        html.Img(src='assets/logo.png', style={'height': '100px', 'margin-left': 'auto', 'margin-right': 'auto'}),
    ], style={'text-align': 'center', 'margin-bottom': '10px'}),

    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='Upload de Arquivo', value='tab-upload'),
        dcc.Tab(label='Gráfico 2D', value='tab-2d'),
        dcc.Tab(label='Gráfico 3D', value='tab-3d'),
    ], value='tab-upload'),
    html.Div(id='tabs-content'),
    dcc.Store(id='store-data')  # Componente para armazenar os dados
])

@app.callback(Output('tabs-content', 'children'),
              Input('tabs', 'value'),
              State('store-data', 'data'))
def render_content(tab, data):
    if tab == 'tab-upload':
        return html.Div([
            dcc.Upload(
                id='upload-data',
                children=html.Div(['Arraste ou ', html.A('selecione um arquivo Excel')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                    'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
            html.Br(),
            dbc.Spinner(spinner_style={"width": "3rem", "height": "3rem"}, children=[html.Div(id="macro-output")]),
            html.Div([
                html.Br(),
                html.Iframe(id='html-viewer', src="", width='80%', height='600'),
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '10px'}),

        ])
    elif tab == 'tab-2d' and data is not None:
        df = pd.read_json(data, orient='split')
        options = [{'label': i, 'value': i} for i in df.columns]
        return html.Div([
            dcc.Dropdown(id='x-axis-column-2d', options=options),
            dcc.Dropdown(id='y-axis-column-2d', options=options),
            dcc.Graph(id='graph-2d', style={'height': '600px', 'width': '100%'}),
        ])
    elif tab == 'tab-3d' and data is not None:
        df = pd.read_json(data, orient='split')
        options = [{'label': i, 'value': i} for i in df.columns]
        return html.Div([
            dcc.Dropdown(id='x-axis-column-3d', options=options),
            dcc.Dropdown(id='y-axis-column-3d', options=options),
            dcc.Dropdown(id='z-axis-column-3d', options=options),
            dcc.Graph(id='graph-3d', style={'height': '600px', 'width': '100%'}),
        ])
    return html.Div("Por favor, selecione um arquivo na aba 'Upload de Arquivo'.")

@app.callback(
    Output('store-data', 'data'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    prevent_initial_call=True
)
def store_data(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if isinstance(df, pd.DataFrame):
            return df.to_json(date_format='iso', orient='split')
    return None

@app.callback(
    Output('graph-2d', 'figure'),
    [Input('x-axis-column-2d', 'value'),
     Input('y-axis-column-2d', 'value')],
    State('store-data', 'data')
)
def update_graph_2d(xaxis_column_name, yaxis_column_name, data):
    if data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        if xaxis_column_name and yaxis_column_name:
            return {
                'data': [go.Scatter(
                    x=df[xaxis_column_name],
                    y=df[yaxis_column_name],
                    mode='markers'
                )],
                'layout': go.Layout(
                    xaxis={'title': xaxis_column_name},
                    yaxis={'title': yaxis_column_name},
                    margin={'l': 40, 'b': 40, 't': 10, 'r': 10},
                    hovermode='closest'
                )
            }
    return {'data': []}

@app.callback(
    Output('graph-3d', 'figure'),
    [Input('x-axis-column-3d', 'value'),
     Input('y-axis-column-3d', 'value'),
     Input('z-axis-column-3d', 'value')],
    State('store-data', 'data')
)
def update_graph_3d(xaxis_column_name, yaxis_column_name, zaxis_column_name, data):
    if data:
        df = pd.read_json(StringIO(data), orient='split')
        if xaxis_column_name and yaxis_column_name and zaxis_column_name:
            df[xaxis_column_name] = pd.to_numeric(df[xaxis_column_name], errors='coerce')
            df[yaxis_column_name] = pd.to_numeric(df[yaxis_column_name], errors='coerce')
            df[zaxis_column_name] = pd.to_numeric(df[zaxis_column_name], errors='coerce')

            # Preparação dos dados para o gráfico 3D
            x_unique = np.linspace(df[xaxis_column_name].min(), df[xaxis_column_name].max(), num=500)
            y_unique = np.linspace(df[yaxis_column_name].min(), df[yaxis_column_name].max(), num=500)
            x_grid, y_grid = np.meshgrid(x_unique, y_unique)
            z_grid = griddata(
                (df[xaxis_column_name], df[yaxis_column_name]),
                df[zaxis_column_name],
                (x_grid, y_grid),
                method='cubic'
            )

            return {
                'data': [go.Surface(z=z_grid, x=x_unique, y=y_unique)],
                'layout': go.Layout(
                    autosize=True,
                    margin=dict(l=50, r=50, b=30, t=30, pad=4),  # Ajusta as margens aqui
                    scene=dict(
                        xaxis=dict(title=xaxis_column_name),
                        yaxis=dict(title=yaxis_column_name),
                        zaxis=dict(title=zaxis_column_name),
                        aspectmode='cube',
                    )
                )
            }
    return {'data': []}

def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
    try:
        if 'xlsx' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
            df = df.drop('Experiment', axis=1)
        else:
            return None
        return df
    except Exception as e:
        print(e)
        return None

@app.callback([Output('html-viewer', 'src', allow_duplicate=True),
               Output("macro-output", "children", allow_duplicate=True),],
              [Input('upload-data', 'contents')],
              [State('upload-data', 'filename')],
              prevent_initial_call=True
              )


def update_output(contents, filename):
    if contents is not None:
        df = parse_contents(contents, filename)
        if df is not None:
            data_analytics(df)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            Html_Page = f"assets/relatorio_analise.html?update={timestamp}"
            return Html_Page, ""
        else:
            Html_Page = ""
            return Html_Page, ""

    Html_Page = ""
    return Html_Page, ""


if __name__ == '__main__':
    app.run_server(host='127.0.0.3', port=8080, debug=False)
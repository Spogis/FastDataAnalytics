import base64
import io
import dash
from dash import dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import numpy as np
from scipy.interpolate import griddata
from datetime import datetime
from io import StringIO
from pykrige.ok import OrdinaryKriging

from analytics_app.DataAnalytics import *
from analytics_app.Kriging import *

# Inicializa o app Dash
app = dash.Dash(__name__,
                suppress_callback_exceptions=True,
                external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1.0"}],)

app.title = "Fast Data Analytics"
server = app.server


app.title = "Data Explorer - Profile Report and EDA App"

server = app.server

# Layout do aplicativo
app.layout = html.Div([
    html.Div([
        html.Img(src='assets/logo.png', style={'height': '100px', 'margin-left': 'auto', 'margin-right': 'auto'}),
    ], style={'text-align': 'center', 'margin-bottom': '10px'}),

    dcc.Tabs(id="tabs", children=[
        dcc.Tab(label='File Upload', value='tab-upload'),
        dcc.Tab(label='Profile Report', value='tab-report'),
        dcc.Tab(label='2D Chart', value='tab-2d'),
        dcc.Tab(label='3D Chart', value='tab-3d'),
        dcc.Tab(label='Kriging Interpolation', value='tab-kriging'),
        dcc.Tab(label='Parallel Coordinates Plot', value='tab-parcoords'),
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
                children=html.Div(['Drag or ', html.A('select an Excel file')]),
                style={
                    'width': '100%', 'height': '60px', 'lineHeight': '60px',
                    'borderWidth': '1px', 'borderStyle': 'dashed', 'borderRadius': '5px',
                    'textAlign': 'center', 'margin': '10px'
                },
                multiple=False
            ),
        ])
    elif tab == 'tab-report' and data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        return html.Div([
            html.Div([
                html.Br(),
                html.Button('Create Report', id='create-report-btn', n_clicks=0,
                            style={'backgroundColor': 'orange', 'color': 'white', 'fontWeight': 'bold', 'fontSize': '20px',
                                   'marginRight': '10px'}),
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '10px'}),

            html.Br(),
            dbc.Spinner(spinner_style={"width": "3rem", "height": "3rem"}, children=[html.Div(id="macro-output")]),
            html.Div([
                html.Br(),
                html.Iframe(id='html-viewer', src="", width='80%', height='600'),
            ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '10px'}),
        ])
    elif tab == 'tab-2d' and data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        options = [{'label': i, 'value': i} for i in df.columns]
        return html.Div([
            dcc.Dropdown(id='x-axis-column-2d', options=options),
            dcc.Dropdown(id='y-axis-column-2d', options=options),
            dcc.Graph(id='graph-2d', style={'height': '600px', 'width': '100%'}),
        ])
    elif tab == 'tab-3d' and data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        options = [{'label': i, 'value': i} for i in df.columns]
        return html.Div([
            dcc.Dropdown(id='x-axis-column-3d', options=options),
            dcc.Dropdown(id='y-axis-column-3d', options=options),
            dcc.Dropdown(id='z-axis-column-3d', options=options),
            dcc.Graph(id='graph-3d', style={'height': '600px', 'width': '100%'}),
        ])
    elif tab == 'tab-parcoords' and data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        return html.Div([
            dcc.Graph(id='graph-parcoords'),
        ])
    elif tab == 'tab-kriging' and data is not None:
        df = pd.read_json(StringIO(data), orient='split')
        options = [{'label': i, 'value': i} for i in df.columns]
        return html.Div([
            html.Div([
                html.H4('Select the 2 Independent Variables', style={'text-align': 'center'}),
                dcc.Dropdown(id='independent-vars-3d', options=options, multi=True, value=[],
                             style={'width': '400px', 'margin': '0 auto'}),
            ], style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center', 'justifyContent': 'center',
                      'marginBottom': '10px'}),

            html.Div([
                html.Br(),
                html.H4('Select the Dependent Variable (1 variable)', style={'text-align': 'center'}),
                dcc.Dropdown(id='dependent-var-3d', options=options, multi=False, value=None,
                             style={'width': '400px', 'margin': '0 auto'}),
            ], style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center', 'justifyContent': 'center',
                      'marginBottom': '10px'}),

            html.Div([
                html.Br(),
                html.Button('Generate Kriging Interpolation', id='generate-kriging-3d', n_clicks=0,
                            style={'backgroundColor': 'orange', 'color': 'white', 'fontWeight': 'bold',
                                   'fontSize': '20px',
                                   'marginRight': '10px'}
                            ),
                html.Br(),
                html.Div(id='kriging-plot-output-3d')
            ], style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center', 'justifyContent': 'center',
                      'marginBottom': '10px'}),
        ], style={'display': 'flex', 'flex-direction': 'column', 'alignItems': 'center', 'justifyContent': 'center',
                  'width': '100%'})

    return html.Div([
        html.Br(),
        html.H2("Please select a file in the 'File Upload' tab.")
    ], style={'display': 'flex', 'justifyContent': 'center', 'alignItems': 'center', 'marginBottom': '10px'}),

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
                    margin=dict(l=50, r=50, b=30, t=30, pad=4),
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
        else:
            return None
        return df
    except Exception as e:
        print(e)
        return None


@app.callback([Output('html-viewer', 'src', allow_duplicate=True),
               Output("macro-output", "children", allow_duplicate=True),],
              Input('create-report-btn', 'n_clicks'),
              [State('store-data', 'data')],
              prevent_initial_call=True
              )


def update_output(n_clicks, data):
    if data:
        df = pd.read_json(StringIO(data), orient='split')
        if df is not None:
            data_analytics(df)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            Html_Page = f"assets/relatorio_analise.html?update={timestamp}"
            return Html_Page, ""
        else:
            Html_Page = ""
            return Html_Page, ""
    else:
        Html_Page = ""
        return Html_Page, ""

@app.callback(
    Output('graph-parcoords', 'figure'),
    [Input('store-data', 'data')]
)
def update_graph_parcoords(data):
    if data:
        df = pd.read_json(StringIO(data), orient='split')
        fig = px.parallel_coordinates(df, color=df.columns[-1])
        return fig
    return go.Figure()


@app.callback(
    Output('kriging-plot-output-3d', 'children'),  # Assumindo que você tenha um componente para o plot
    [Input('generate-kriging-3d', 'n_clicks')],
    [State('independent-vars-3d', 'value'),
     State('dependent-var-3d', 'value'),
     State('store-data', 'data')]
)
def update_kriging_plot(n_clicks, independent_vars, dependent_var, data):
    if n_clicks > 0 and data is not None and len(independent_vars) == 2 and dependent_var is not None:
        df = pd.read_json(StringIO(data), orient='split')
        # Realiza a interpolação Kriging
        OK3D, gridx, gridy, z, ss = perform_kriging_3d(independent_vars, dependent_var, df)

        # Cria um gráfico de superfície com os resultados da interpolação
        fig = go.Figure(data=[go.Surface(z=z, x=gridx, y=gridy)])

        fig.update_layout(autosize=True,
                          scene=dict(
                              xaxis_title=independent_vars[0],
                              yaxis_title=independent_vars[1],
                              zaxis_title=dependent_var,
                              aspectmode='cube'
                          ),
                          margin=dict(l=50, r=50, b=30, t=30, pad=4),
                          height=600,
                          width=800,
                          )

        return dcc.Graph(figure=fig)

    return "Select two independent variables and one dependent variable and click 'Generate Kriging Interpolation' to see the result."

if __name__ == '__main__':
    app.run_server(host='127.0.0.3', port=8080, debug=False)

import os
import sys

import dash
import dash_bootstrap_components as dbc
import dash_leaflet as dl
import osmnx as ox
from dash import dash_table, dcc, html

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.llm_agent import run_llm  # noqa: F401

#import dash_html_components as html
from src.routing import get_nodes_on_road  # noqa: F401

# Load the graph object (should make this user selectable for final app)
# G_tolworth = ox.graph_from_point((51.3829463, -0.2933327), dist=5000, network_type='drive')
# ox.save_graphml(G_tolworth, filepath="data/tolworth.graphml")
G = ox.load_graphml("data/tolworth.graphml")

# Sample directions data
directions_data = [
    {"Step": "", "Current Road": "", "Next Road": "", "Instruction": ""},

]

# Create Dash app with Bootstrap stylesheet
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Navigation Assistant"

# Layout
app.layout = dbc.Container(fluid=True, children=[
    dbc.Row([
        # Left Column: Map
        dbc.Col(width=7, children=[
            dl.Map(
                center=[51.3829, -0.2933],  # Tolworth area
                zoom=15,
                children=[
                    dl.TileLayer(),
                    dl.LayerGroup(id="route-layer")
                    # Add any markers or layers here
                ],
                style={'width': '100%', 'height': '90vh'}
            )
        ]),

        # Right Column: Directions and Controls
        # Right Column: Directions, Terminal, and Controls
        dbc.Col(width=5, children=[
            html.H4("Directions"),
            
            # Add near top of right column:
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    '📁 Drag and Drop or ',
                    html.A('Select CSV File')
                ]),
                style={
                    'width': '100%',
                    'height': '60px',
                    'lineHeight': '60px',
                    'borderWidth': '1px',
                    'borderStyle': 'dashed',
                    'borderRadius': '5px',
                    'textAlign': 'center',
                    'marginBottom': '10px'
                },
                multiple=False
            ),

            # Hidden data store
            dcc.Store(id='directions-df'),
            dcc.Store(id='route_nodes'),
            
            dash_table.DataTable(
                id="directions-table",
                columns=[{"name": i, "id": i} for i in ["Step", "Current Road", "Next Road", "Instruction"]],
                data=directions_data,
                style_cell={'textAlign': 'left', 'padding': '5px'},
                style_header={'fontWeight': 'bold'},
                style_table={'height': '300px', 'overflowY': 'auto'}
            ),
            html.Br(),

            html.H5("Terminal Output"),
            html.Pre(
                id="terminal-output",
                children="> System ready.\n> Awaiting LLM response...",
                style={
                    'backgroundColor': '#111',
                    'color': '#0f0',
                    'padding': '10px',
                    'height': '200px',
                    'overflowY': 'scroll',
                    'borderRadius': '5px',
                    'fontFamily': 'monospace',
                    'fontSize': '14px',
                    'whiteSpace': 'pre-wrap'
                }
            ),
            
            html.Div([
            html.Label("Initial Node Number:", style={"fontWeight": "bold"}),
            dcc.Input(
                id="initial-node-input",
                type="number",
                placeholder="Enter start node (e.g. 12345)",
                style={"width": "100%", "marginBottom": "10px"}
            )
            ]),

            dbc.ButtonGroup([
                dbc.Button("Process Step", id="process-step-btn", color="secondary"),
                #dbc.Button("Next", id="next-button", color="primary")
            ], className="mt-3")
        ])

    ])
])

# Register callbacks
from callbacks import upload_callbacks, llm_callbacks  # noqa

if __name__ == '__main__':
    app.run(debug=True, port=8052)

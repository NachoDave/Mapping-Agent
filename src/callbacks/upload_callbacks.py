# src/callbacks/upload_callbacks.py

import base64
import io

import dash
import pandas as pd
from dash import Input, Output, State, callback


@callback(
    Output("directions-df", "data"),         # hidden store component (holds full DataFrame)
    #Output("directions-table", "data"),      # updates the DataTable
    Input("upload-data", "contents"),        # file upload component
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def handle_csv_upload(contents, filename):
    if contents is None:
        return dash.no_update

    # Decode CSV content
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

    # Validate required columns
    if 'Current Road' not in df.columns or 'Instruction' not in df.columns:
        raise ValueError("CSV must contain 'Current Road' and 'Instruction' columns.")

    # Generate 'Next Road' and empty 'Tool Call' column
    df['Next Road'] = df['Current Road'].shift(-1)
    df['Tool Call'] = ""

    # Add Step number
    df.insert(0, 'Step', range(1, len(df) + 1))

    # Return both table data and full data as JSON
    return df.to_dict('records')  #, df.to_dict('records')


@callback(
    Output("directions-table", "data"),
    Input("directions-df", "data")
)
def update_table_from_store(store_data):
    return store_data

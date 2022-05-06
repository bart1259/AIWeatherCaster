import os
from flask import Flask, send_from_directory
import numpy as np
import json

from .utils import numpy_json_serializer
from .forecaster import get_forecast

app = Flask(__name__)

@app.route('/alive')
def alive_route():
    return 'Yes'

@app.route('/getForecast')
def forecast():
    forcast_data = get_forecast(3)
    json_forecast = json.dumps(forcast_data, default=numpy_json_serializer)
    return json_forecast

# Serve up index.html
@app.route('/')
def index():
    root_dir = str(os.getcwd())
    return send_from_directory(root_dir + "\\frontend", "index.html")

# Serve up frontned
@app.route('/<path:path>')
def frontend(path):
    root_dir = str(os.getcwd())
    return send_from_directory(root_dir + "\\frontend", path)
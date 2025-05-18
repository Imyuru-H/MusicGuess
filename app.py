# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

# third party module initlization
import __init__

"""A simple app for Rhythm Game Music guessing game.

Author:      Imyuru_ (Imyuru_H)
Version:     0.0.2
Update Time: 25/05/18
"""

"""Update Log:
0.0.1:
 - Construct basic functions.
0.0.2:
 - Realize song info crawl and display.
"""

__version__ = '0.0.2'
__author__ = 'Imyuru_'

# Copyright (c) 2025 Imyuru_. Licensed under MIT License.

import os, sys, time, random
os.environ["PYTHONIOENCODING"] = "utf-8"
start_time = time.time()

import numpy as np
from flask import *
import logging
import queue
import threading
from PyQt5.QtWidgets import QApplication

import NonUiLog, UiLog
import crawler


# config app settings
CONFIGS = {
    'ui_logging' : True,
    'flask_debug' : False,
    'flask_port' : 1145,
    'app_name' : 'Firefly',
    'templates_reload' : True
}
    
# init log
app_qt = QApplication([])
if CONFIGS['ui_logging']:
    logs = UiLog.LoggerApp()
else:
    logs = NonUiLog.Info()
    
# init crawler
phi_crawler = crawler.PhiCrawler()

# init flask app
app = Flask(CONFIGS['app_name'])
app.config['TEMPLATES_AUTO_RELOAD'] = CONFIGS['templates_reload']
app.static_folder = "static"

# Config Flask logging handlers
app.logger.handlers = []

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = []  # Clear all handlers
werkzeug_logger.propagate = False  # Deny log propagete
werkzeug_logger.setLevel(logging.CRITICAL)  # Set log level

log_queue = queue.Queue(-1) # Unlimited queue

# Process logs
@app.after_request
def capture_response_data(response):
    # Define the mapping between status code and log level
    STATUS_LOG_MAP = {
        2: "info",
        3: "info",
        4: "error",
        5: "false"
    }
    
    # Get request path, method, status code etc.
    data = {
        "method": request.method,
        "path": request.path,
        "status_code": response.status_code,
        "client_ip": request.remote_addr,
        "user_agent": str(request.user_agent)
    }

    status_category = data.get("status_code", 0) // 100  # Defensive Status Code Retrieval
    log_level = STATUS_LOG_MAP.get(status_category, "error")
    
    # Dynamically retrieve logging methods to avoid AttributeError caused by typos
    log_method = getattr(logs, log_level, logs.error)
    log_content = f"- {data['method']} {data['status_code']} - from {data['client_ip']}, calling {data['path']}"
    log_method(f"Status {data['status_code']}: {log_content}", if_linkify=False)
    
    return response


# define flask app routes
@app.route('/')
def index():
    return render_template("home.html")

@app.route('/single')
def single():
    return render_template("single.html")

@app.route('/submit', methods=['POST'])
def parse_data():
    if not request.is_json:  # Check if Content-Type is application/json
        return jsonify({"error": "Unsupported Media Type: 需要 JSON 数据"}), 415
    
    data = request.get_json()
    if not data:
        logs.info(f"User Input: No input")
        return jsonify({'status': False}), 400
    
    title = data.get('title')
    if title == "":
        logs.info("User Input: None")
        return jsonify({'status': False})
    
    logs.info(f"User Input: {title}")
    data, duration = phi_crawler.run(title)
    logs.info("Crawler:",
              f" - Song data: {data}",
              f" - Time cost: {duration:.2f} Seconds")
    return jsonify(dict({'status': True, 'title': title}, **data))


if __name__ == "__main__":
    end_time = time.time()
    logs.info(f"App start duration: {end_time-start_time:.2f}s")
    
    def run_flask_app():
        app.run(debug=CONFIGS['flask_debug'], 
                use_reloader=False, 
                port=CONFIGS['flask_port'])
    
    def crawler_init():
        start_time = time.time()
        moe_crawler = crawler.MoeCrawler()
        moe_crawler._fetch(crawler.Config.START_URL_MOE)
        logs.info(f"Crawler initialize over. Duration: {(time.time() - start_time):.2f} seconds")
    
    # Define flask thread
    flask_thread = threading.Thread(target=run_flask_app, daemon=True)
    # Define Crawler init thread
    crawler_init_thread = threading.Thread(target=crawler_init)
    
    # Start Flask app's thread
    flask_thread.start()
    logs.info(f" * Serving Flask app '{CONFIGS['app_name']}' on 127.0.0.1:{CONFIGS['flask_port']}",
              f" * Debug mode: {'on' if CONFIGS['flask_debug'] else 'off'}")
    # Start Crawler init thread
    crawler_init_thread.start()
    
    # Show Logging window and start Qt event loop
    logs.show()
    sys.exit(app_qt.exec_())
# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

# third party module initlization
import __init__

"""A simple app for Rhythm Game Music guessing game.

Author:      Imyuru_ (Imyuru_H)
Version:     0.0.3
Update Time: 25/05/25
"""

"""Update Log:
0.0.1:
 - Construct basic functions.
0.0.2:
 - Realize song info crawl and display.
0.0.3:
 - Fix bugs for some possible situation.
 - Realize nick name identify.
"""

__version__ = '0.0.3'
__author__ = 'Imyuru_'

# Copyright (c) 2025 Imyuru_. Licensed under MIT License.

import os, sys, time, random
os.environ["PYTHONIOENCODING"] = "utf-8"
start_time = time.time()

# import numpy as np
from flask import *
import pandas as pd
import logging
import queue
import threading
from PyQt5.QtWidgets import QApplication

import NonUiLog, UiLog
import crawler


# config app settings
CONFIGS = {
    'ui_logging' : True,
    'show_log' : True,
    'flask_debug' : False,
    'flask_port' : 1145,
    'app_name' : 'Firefly',
    'templates_reload' : True
}
    
# init log
app_qt = QApplication([])
if CONFIGS['ui_logging']:
    logs = UiLog.LoggerApp(show_ui=CONFIGS['show_log'])
else:
    logs = NonUiLog.Info()
logs.info("Logger app init done.")
    
# init crawler
phi_crawler = crawler.PhiCrawler()
logs.info("Crawler init done.")

# init quest bank
def init_quest() -> tuple[list[str], dict[str, list[str]]]:
    quest_bank:pd.DataFrame = pd.read_excel('static\\quest_bank\\quest_phigros.xlsx',
                                            sheet_name='quest_phigros')
    
    titles:list[str] = [str(nick) for nick in quest_bank['name'].values]
    
    nicks:list[list[str]] = [([] if nick == 'nan' else nick.split(';')) for nick in [str(nick) for nick in quest_bank['nick name'].values]]
    
    nick_dict:dict = {titles[i]:[titles[i].lower()] + [nick.lower() for nick in nicks[i]] for i in range(len(titles))}
    
    return titles, nick_dict

title_lst, nick_dict = init_quest()
logs.info("Quest bank init done.")

# init flask app
app = Flask(CONFIGS['app_name'])
app.config['TEMPLATES_AUTO_RELOAD'] = CONFIGS['templates_reload']
app.static_folder = "static"
logs.info("Flask app init done.")

# Config Flask logging handlers
app.logger.handlers = []

werkzeug_logger = logging.getLogger('werkzeug')
werkzeug_logger.handlers = []  # Clear all handlers
werkzeug_logger.propagate = False  # Deny log propagete
werkzeug_logger.setLevel(logging.CRITICAL)  # Set log level

log_queue = queue.Queue(-1) # Unlimited queue
logs.info("Flask logging handlers init done.")

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

@app.route('/start', methods=['POST'])
def start():
    global title_lst
    
    return jsonify({'operation': 'game start', 'status': True, 'quest': 'start'})

@app.route('/submit', methods=['POST'])
def parse_data():
    def _find_all_keys(d:dict[str, list[str]], target:str) -> list[str]:
        return [key for key, lst in d.items() if target in lst]

    global nick_dict
    
    if not request.is_json:  # Check if Content-Type is application/json
        return jsonify({"error": "Unsupported Media Type: 需要 JSON 数据"}), 415
    
    data = request.get_json()
    if not data:
        logs.info(f"User Input: No input")
        return jsonify({'operation': 'input submit', 'status': False}), 400
    
    title:str = data.get('title')
    if title == "":
        logs.info("User Input: None")
        return jsonify({'operation': 'input submit', 'status': False})
    
    logs.info(f"User Input: {title}")
    title:list[str] = _find_all_keys(nick_dict, title.lower())
    logs.info(f" -> {title}")
    
    if len(title) == 1:
        try:
            data, duration = phi_crawler.run(title[0])
            data = [data]
        except AttributeError as e:
            print(e)
            return jsonify({'operation': 'input submit', 'error':'没有这个别名哦喵~', 'status': False})
    else:
        return jsonify({'operation': 'input submit', 'status': True, 'title': title})
    
    logs.info("Crawler:",
              *[f" - Song data {data.index(d)}: {d}" for d in data],
              f" - Time cost: {duration:.2f} Seconds")
    
    html = [f"""
<tr id="column">
    <td>{title[i]}</td>
    <td>{data[i]['artist']}</td>
    <td>{data[i]['bpm']}</td>
    <td>{"✅" if len(data[i]['level']) == 4 else "❌"}</td>
    <td>
        <span>{data[i]['level'][0]}</span>
        <span>{data[i]['level'][1]}</span>
        <span>{data[i]['level'][2]}</span>
        {f"<span>{data[i]['level'][3]}</span>" if len(data[i]['level']) == 4 else ''}
    </td>
    <td>{data[i]['note count'][-1]}</td>
    <td>{data[i]['pack']}</td>
</tr>""" for i in range(len(data))]

    logs.info(*html)
    
    return jsonify({'operation': 'input submit', 'status': True, 'html': html, 'title': title})


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
    if CONFIGS['ui_logging']:
        logs.show()
        sys.exit(app_qt.exec_())
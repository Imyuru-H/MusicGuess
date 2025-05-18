# !/.venv/Scripts python3
# -*- coding: utf-8 -*-


__version__ = '0.4.0'

"""
+------------------+------------+
| Author           | Imyuru_    |
| Version          | 0.4.0      |
| Last update time | 2025-3-29  |
+------------------+------------+

Update Features:
 - rebuild the app with PyQt5 from tkinter.
 - 增加可操控的链接识别并转化为超链接
"""


import os
import sys
import re
from html import escape
from urllib.parse import urlparse

os.environ["PYTHONIOENCODING"] = "utf-8"

import numpy as np


from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget,
                             QVBoxLayout, QHBoxLayout, QLabel, 
                             QTextBrowser, QLineEdit, QSizePolicy,
                             QSystemTrayIcon, QMenu)
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import (QThread, pyqtSignal, pyqtSlot,
                          QMutex, Qt, QEasingCurve,
                          QEvent, QPropertyAnimation, pyqtProperty)
from PyQt5.QtGui import QIcon, QPixmap

import platform
import psutil
import cpuinfo
import GPUtil
from prettytable import PrettyTable
from datetime import datetime

# Check OS type
if os.name == 'nt':  # Windows
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")
else:  # macOS & Linux
    pass

CONFIG = {
    'app_name' : 'LoggerApp',
    'window_size' : (1280, 720),
    'font_family' : 'Consolas',
    'font_size' : 10
}


class LogConsumer(QThread):
    log_received = pyqtSignal(str, str, bool)  # (log_type, message, if_linkify)
    stats_updated = pyqtSignal(dict)     # counters dict

    def __init__(self):
        super().__init__()
        self.running = True
        self.mutex = QMutex()
        self.log_queue = []
        self.counters = {
            'info': 0,
            'error': 0,
            'false': 0,
            'debug': 0,
            'input': 0            
        }
    
    def push_log(self, log_type:str, message:str, if_linkify:bool) -> None:
        self.mutex.lock()
        self.log_queue.append((log_type, message, if_linkify))
        self.mutex.unlock()

    def run(self) -> None:
        while self.running:
            self.mutex.lock()
            if self.log_queue:
                log_type, message, if_linkify = self.log_queue.pop(0)
                self.counters[log_type] += 1
                self.log_received.emit(log_type, message, if_linkify)
                self.stats_updated.emit(self.counters.copy())
            self.mutex.unlock()
            self.msleep(1)

    def stop(self) -> None:
        self.running = False
        self.wait()


class LoggerApp(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._init_worker()
        self.info("System Info:", *self.get_sys_info())
    
    def _init_ui(self):
        self.setWindowTitle(CONFIG['app_name'])
        self.setGeometry(100, 100, *(CONFIG['window_size']))
        
        ico_path = os.path.join(os.path.dirname(__file__), 'logAppIcon.png')
        icon = QIcon()
        icon.addPixmap(QPixmap(ico_path), QIcon.Normal, QIcon.Off)
        self.setWindowIcon(icon)

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(0)
        
        # Log display
        self.log_text = QTextBrowser()
        self.log_text.setReadOnly(True)
        self.log_text.setOpenExternalLinks(True)
        self.log_text.setStyleSheet("""
            QTextBrowser:focus {
                border: 1px solid #7A7A7A;
            }
            a { color: #000000; text-decoration: none; }
            a:hover { text-decoration: underline; }
            a:visited { border: none }
        """)
        
        main_layout.addWidget(self.log_text)
        
        # input panel
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Input command...")
        self.input_field.returnPressed.connect(self.handle_submit)
        self.input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_field.setStyleSheet("""
            QLineEdit {
                border-top: 0px solid #101010;
                border-bottom: 1px solid #7A7A7A;
                border-left: 1px solid #7A7A7A;
                border-right: 1px solid #7A7A7A;
                padding: 2px;
            }
        """)
        
        main_layout.addWidget(self.input_field)

        # Stats panel
        stats_widget = QWidget()
        stats_layout = QHBoxLayout(stats_widget)
        self.stats_labels = {
            'info' : QLabel("INFO: 0" ),
            'error': QLabel("ERROR: 0"),
            'false': QLabel("FALSE: 0"),
            'debug': QLabel("DEBUG: 0"),
            'input': QLabel("INPUT: 0")
        }
        for label in self.stats_labels.values():
            stats_layout.addWidget(label)
        
        main_layout.addWidget(stats_widget)

    def _init_worker(self):
        self.consumer = LogConsumer()
        self.consumer.log_received.connect(self.append_log)
        self.consumer.stats_updated.connect(self.update_stats)
        self.consumer.start()

    def get_sys_info(self):
        info = {
            "OS Info" : f"{platform.system()} {platform.release()}",
            "Python Version" : platform.python_version(),
            "CPU" : f"{cpuinfo.get_cpu_info()['brand_raw']} × {psutil.cpu_count(logical=False)} ",
            "RAM" : f"{psutil.virtual_memory().total//(1024**3):.2f} GB"
        }
        try:
            gpus = GPUtil.getGPUs()
            for i, gpu in enumerate(gpus):
                info[f"GPU {i}"] = f"{gpu.name}"
                info[f"VRAM {i}"] = f"{gpu.memoryTotal} MB"
        except:
            info["GPU"] = "Not Available"
        
        table = PrettyTable(['1','2'])
        for kwargs in info.items():
            table.add_row([*kwargs])

        table = str(table).split("\n")

        # Replace space into invisible placeholder
        special_char = "\u200B"
        for i in range(len(table)):
            table[i] = table[i].replace(" ", special_char + " ")

        return table

    def _linkify_text(self, text: str) -> str:
        """将文本中的 IP 和 URL 转换为超链接"""
        # Precompile regular expressions
        ip_pattern = re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}(?::\d+)?\b')  # Handle URLs with ports (e.g. 192.168.1.1:8080)
        url_pattern = re.compile(
            r'(?:https?|ftp)://[^\s,]+|'  # Match URLs with protocols
            r'\b(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?::\d+)?(?:/[^\s,]+)?\b'  # Match pure domain names with ports and paths (e.g. google.com:8080/path)
        )

        def replace_url(match):
            url = match.group(0)
            parsed = urlparse(url)
            if not parsed.scheme:  # Auto-complete the protocol header
                url = f'http://{url}'
            return f'<a href="{url}">{escape(match.group(0))}</a>'

        def replace_ip(match):
            ip = match.group(0)
            return f'<a href="http://{ip}">{escape(ip)}</a>'

        # Process URLs first, then IPs (Avoid duplicate replacements)
        text = url_pattern.sub(replace_url, text)
        text = ip_pattern.sub(replace_ip, text)
        return text

    @pyqtSlot(str, str, bool)
    def append_log(self, log_type: str, message: str, if_linkify:bool):
        color_map = {
            'info' : '#C0C000',
            'error' : '#C03030',
            'false' : '#C00000',
            'debug' : '#C000C0',
            'input' : '#202020',
            'timestamp' : '#858585',
            'content' : '#000000'
        }
        timestamp = datetime.now().strftime("[%H:%M:%S]")
        log_label = f"[{log_type.upper()}]&nbsp;" if log_type == "info" else "&nbsp;&nbsp;>>>&nbsp;&nbsp;" if log_type == "input" else f"[{log_type.upper()}]"

        # Process urls in the message
        processed_msg = self._linkify_text(escape(message)) if if_linkify else message

        log_html = f"""
            <div style="margin-bottom: 2px;
                        line-height: 1.4em;
                        font-family: {CONFIG['font_family']};
                        font-size: {CONFIG['font_size']}pt;
                        border-bottom: 1px solid #101010;
                        padding: 1px 0;">
                <span style="color: {color_map['timestamp']}">{timestamp}</span>
                <span style="color: {color_map[log_type]}">{log_label}</span>
                <span style="color: {color_map['content']}">{processed_msg}</span>
            </div>
        """
        self.log_text.moveCursor(QTextCursor.End)
        self.log_text.insertHtml(log_html)
        self.log_text.insertPlainText("\n")
        self.log_text.ensureCursorVisible()
    
    @pyqtSlot(dict)
    def update_stats(self, counters: dict):
        for log_type, count in counters.items():
            self.stats_labels[log_type].setText(
                f"{log_type.upper()}: {count}"
            )
            
    def handle_submit(self):
        cmd = self.input_field.text()
        self.input(cmd)
        self.input_field.clear()
    
    def closeEvent(self, event):
        if hasattr(self, 'consumer'):
            self.consumer.stop()
        return super().closeEvent(event)
    
    # Public API methods
    def info(self, *messages, if_linkify=True):
        for message in messages:
            self.consumer.push_log('info', str(message), if_linkify)
    
    def error(self, *messages, if_linkify=True):
        for message in messages:
            self.consumer.push_log('error', str(message), if_linkify)

    def false(self, *messages, if_linkify=True):
        for message in messages:
            self.consumer.push_log('false', str(message), if_linkify)

    def debug(self, *messages, if_linkify=True):
        for message in messages:
            self.consumer.push_log('debug', str(message), if_linkify)
    
    def input(self, message, if_linkify=True):
        self.consumer.push_log('input', str(message), if_linkify)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    logs = LoggerApp()
    logs.show()
    
    # Test
    logs.info("https://example.com 或 IP 192.168.1.1:8080")
    logs.error("ftp://ftp.test.org/file.txt")
    logs.debug("127.0.0.1")
    logs.input("curl http://api.demo.com/v1/data")
    
    sys.exit(app.exec_())
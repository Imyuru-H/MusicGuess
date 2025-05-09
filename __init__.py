# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

"""
This python module use to install necessary libraries for the web app.
"""

import os, platform


_path = ".\\.venv\\Scripts\\"

if platform.python_version().split(".")[1] > '11':
    os.system(f"{_path}pip.exe install setuptools")

os.system(f"{_path}pip.exe install -r requirements.txt")
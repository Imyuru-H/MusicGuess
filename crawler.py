# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

"""A crawler for Rhythm Game Music guessing game.

Author:      Imyuru_ (Imyuru_H)
Version:     0.0.1
Update Time: 25/05/09
"""

__version__ = '0.0.1'
__author__ = 'Imyuru_'

# Copyright (c) 2025 Imyuru_. Licensed under MIT License.

import os, sys, time, random
os.environ["PYTHONIOENCODING"] = "utf-8"

import requests
from bs4 import BeautifulSoup
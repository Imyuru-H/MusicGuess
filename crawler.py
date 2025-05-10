# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

"""A crawler for Rhythm Game Music guessing game.

Author:      Imyuru_ (Imyuru_H)
Version:     0.0.2
Update Time: 25/05/09
"""

__version__ = '0.0.2'
__author__ = 'Imyuru_'

# Copyright (c) 2025 Imyuru_. Licensed under MIT License.

import os, sys, time, random
os.environ["PYTHONIOENCODING"] = "utf-8"

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin


class Config:
    BASE_URL = "https://phigros.fandom.com/"
    START_URL = "https://phigros.fandom.com/wiki/"
    HEADERS = {
        "User-Agent": UserAgent().random,
        "Accept-Language": "en-US,en;q=0.9",
    }
    TIMEOUT = 10
    MAX_RETRY = 3

class Crawler:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(Config.HEADERS)
        self.visited_urls = set()
    
    def _fetch(self, url:str, **kwargs) -> requests.Response:
        for attempt in range(Config.MAX_RETRY):
            try:
                resp = self.session.get(
                    url,
                    timeout=Config.TIMEOUT,
                    **kwargs
                )
                resp.raise_for_status()  # Check HTTP errors
                return resp
            except Exception as e:
                print(f"Fetch failed ({attempt+1}/{Config.MAX_RETRY}): {url} - {str(e)}")
                if attempt == Config.MAX_RETRY - 1:
                    raise
    
    def _parse_html(self, html:requests.Response) -> BeautifulSoup:
        """Parse html pages 解析详情页"""
        soup = BeautifulSoup(html.text, "lxml")
        return soup
    
    def _get_song_data(self, html:BeautifulSoup) -> str:
        table = html.find('table')
        table = table.get_text('')
        return table
    
    def _parse_table_lst(self, table:str) -> dict:
        tb_lst = table.split('\n')
        # del all umpty elements in the list
        tb_lst = list(filter(None, tb_lst))
        if_at = True if tb_lst.index('Difficulty') + 1 - tb_lst.index('Level') == 4 else False # if have AT difficulty then True, if not then False
        
        info_dict = {
            'pack' : tb_lst[tb_lst.index('Pack') + 1],
            'difficulty' : tb_lst[tb_lst.index('Difficulty') + 1 : tb_lst.index('Level')],
            'level' : tb_lst[tb_lst.index('Pack') + 1 : tb_lst.index('Note count')],
            'artist' : tb_lst[tb_lst.index('Artist') + 1],
            'illustration' : tb_lst[tb_lst.index('Illustration') + 1],
            'duration' : tb_lst[tb_lst.index('Duration') + 1],
            'chart design' : list(filter(None, 
                            [tb_lst[tb_lst.index('Chart design (EZ)') + 1],
                             tb_lst[tb_lst.index('Chart design (HD)') + 1],
                             tb_lst[tb_lst.index('Chart design (IN)') + 1],
                             tb_lst[tb_lst.index('Chart design (AT)') + 1] if if_at else '']))
        }
        
        return info_dict
    
    def run(self, song:str) -> dict:
        song = song.replace(' ','_')
        resp = self._fetch(f"{Config.START_URL}{song}")
        data = self._parse_html(resp)
        table = self._get_song_data(data)
        info = self._parse_table_lst(table)
        
        return info


if __name__ == "__main__":
    crawler = Crawler()
    info = crawler.run('Re:End of a Dream')
    print(info)
    
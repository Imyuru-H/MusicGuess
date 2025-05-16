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

import os, re
os.environ["PYTHONIOENCODING"] = "utf-8"

import requests
import bs4
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin


class Config:
    START_URL_MOE = r"https://mzh.moegirl.org.cn/Phigros/%E6%9B%B2%E7%9B%AE%E5%88%97%E8%A1%A8"
    START_URL_WIKI = r"https://phigros.fandom.com/wiki/"
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

class WikiCrawler(Crawler):
    def __init__(self):
        super().__init__()
    
    def _get_song_data(self, html:BeautifulSoup) -> str:
        table = html.find('table')
        table = table.get_text('')
        return table
    
    def _parse_table_lst(self, table:str) -> dict:
        def _get_chart_design(table:list):
            if 'Chart design (EZ)' in table:
                result = list(filter(None, 
                            [tb_lst[tb_lst.index('Chart design (EZ)') + 1],
                             tb_lst[tb_lst.index('Chart design (HD)') + 1],
                             tb_lst[tb_lst.index('Chart design (IN)') + 1],
                             tb_lst[tb_lst.index('Chart design (AT)') + 1] if if_at else '']))
            else:
                result = tb_lst[tb_lst.index('Chart design') + 1]
            
            return result

        tb_lst = table.split('\n')
        # del all umpty elements in the list
        tb_lst = list(filter(None, tb_lst))

        print(tb_lst)

        # if have AT difficulty then True, if not then False
        if_at = True if tb_lst.index('Difficulty') + 1 - tb_lst.index('Level') == 4 else False
        
        info_dict = {
            'pack' : tb_lst[tb_lst.index('Pack') + 1],
            'difficulty' : tb_lst[tb_lst.index('Difficulty') + 1 : tb_lst.index('Level')],
            'level' : tb_lst[tb_lst.index('Level') + 1 : tb_lst.index('Note count')],
            'note count' : tb_lst[tb_lst.index('Note count') + 1 : tb_lst.index('Artist')],
            'artist' : tb_lst[tb_lst.index('Artist') + 1],
            'illustration' : tb_lst[tb_lst.index('Illustration') + 1],
            'duration' : tb_lst[tb_lst.index('Duration') + 1],
            'chart design' : _get_chart_design(tb_lst),
        }
        
        return info_dict
    
    def run(self, song:str) -> dict:
        song = song.replace(' ','_')
        resp = self._fetch(f"{Config.START_URL_WIKI}{song}")
        data = self._parse_html(resp)
        table = self._get_song_data(data)
        info = self._parse_table_lst(table)
        
        return info

class MoeCrawler(Crawler):
    def __init__(self):
        super().__init__()
    
    def _get_n_parse_song_data(self, html:BeautifulSoup) -> dict:
        def get_content(text:str) -> str:
            cleaned_text = re.sub(r'<.*?>', '', text)
            return cleaned_text

        def lst_split(lst:list, step:int) -> list[list]:
            func = lambda a,b : map(lambda c:a[c:c+b],range(0,len(a),b))
            res = list(func(lst, step))
            return res

        def is_valid_format(s):
            pattern = r'^\d+\s+\(\d+\.\d+\)$'
            if re.match(pattern, s):
                return True
            else:
                return False
        
        table = html.find_all('table')

        tb_dict = {
            'main story' : table[1].find_all('td'),
            'side story' : table[2].find_all('td'),
            'ex chapter' : table[3].find_all('td'),
            'ex story' : table[4].find_all('td'),
        }
        
        tmp = []
        for key in tb_dict:
            for elm in tb_dict[key]:
                tmp.append(get_content(str(elm)))
            tb_dict[key] = tmp
            tmp = []
        
        for key in tb_dict:
            tb_dict[key] = [item for item in tb_dict[key] if "\n" not in item and not is_valid_format(item)]
        
        for key in tb_dict:
            tb_dict[key] = lst_split(tb_dict[key],3)
        
        for key in tb_dict:
            for lst in tb_dict[key]:
                tb_dict[key][tb_dict[key].index(lst)] = [lst[0],lst[2]]
        
        bpm_dict = {}
        for key in tb_dict:
            for lst in tb_dict[key]:
                bpm_dict[lst[0]] = lst[1]
        
        return bpm_dict
    
    def run(self, song:str) -> str:
        resp = self._fetch(Config.START_URL_MOE)
        data = self._parse_html(resp)
        bpm_dict = self._get_n_parse_song_data(data)
        bpm = bpm_dict[song]
        
        return bpm

class PhiCrawler:
    def run(self, song:str) -> dict:
        info_crawler = WikiCrawler()
        bpm_crawler = MoeCrawler()
        
        info = info_crawler.run(song)
        info['bpm'] = bpm_crawler.run(song)
        
        return info


if __name__ == "__main__":
    crawler = PhiCrawler()
    info = crawler.run('Spasmodic')
    print(info)
    
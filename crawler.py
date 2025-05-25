# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

""" A crawler for Rhythm Game Music guessing game.

Author:      Imyuru_ (Imyuru_H)
Version:     0.0.5
Update Time: 25/05/25
"""

""" Update Logs:
 - 0.0.1:
     - Create this module and add the basic code.
 - 0.0.2:
     - Divided the public methods of all crawlers into a father class "Crawler"
     - Add a crawler to get the BPM property of the target music.
 - 0.0.3:
     - Fix some bugs while crawling the property which all the charts were wrote by one person.
 - 0.0.4:
     - Add lru_cache to optimize the crawling method.
 - 0.0.5:
     - Fix bugs.
"""

__version__ = '0.0.5'
__author__ = 'Imyuru_'

# Copyright (c) 2025 Imyuru_. Licensed under MIT License.

import os, re, time
from functools import lru_cache
os.environ["PYTHONIOENCODING"] = "utf-8"

import requests
import bs4
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin

from timeit import repeat


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
    
    @lru_cache(maxsize=None)
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
        table = table.get_text(',')
        return table
    
    def _parse_table_lst(self, table:str) -> dict:
        def _get_chart_design(table: list, if_at: bool = False) -> list:
            """
            从表格数据中提取图表设计信息
            
            Args:
                table: 包含图表设计信息的列表
                if_at: 是否包含AT难度信息
                
            Returns:
                提取后的图表设计信息列表
            """
            result = []
            
            # 定义所有可能的键名变体
            KEY_VARIANTS = {
                'ez': ['Chart design (EZ)'],
                'ez_hd': ['Chart design (EZ/HD)'],
                'ez_in': ['Chart design (EZ/IN)'],
                'ez_at': ['Chart design (EZ/AT)'],
                'hd_in': ['Chart design (HD/IN)'],
                'hd_at': ['Chart design (HD/AT)'],
                'in_at': ['Chart design (IN/AT)'],
                'hd': ['Chart design (HD)'],
                'in': ['Chart design (IN)'],
                'at': ['Chart design (AT)'],
                'default': ['Chart design']
            }
            
            def find_key(keys):
                """在表格中查找第一个匹配的键"""
                for key in keys:
                    if key in table:
                        return key
                return None
            
            # 查找存在的键
            found_keys = {k: find_key(v) for k, v in KEY_VARIANTS.items()}
            
            # 确定结果组合
            if found_keys['ez_hd']:
                result = [
                    table[table.index(found_keys['ez_hd']) + 1],
                    table[table.index(found_keys['ez_hd']) + 1],
                    table[table.index(found_keys['in']) + 1] if found_keys['in'] else None,
                    table[table.index(found_keys['at']) + 1] if if_at and found_keys['at'] else None
                ]
            elif found_keys['ez_in']:
                result = [
                    table[table.index(found_keys['ez_in']) + 1],
                    table[table.index(found_keys['hd']) + 1] if found_keys['hd'] else None,
                    table[table.index(found_keys['ez_in']) + 1],
                    table[table.index(found_keys['at']) + 1] if if_at and found_keys['at'] else None
                ]
            elif found_keys['ez_at']:
                result = [
                    table[table.index(found_keys['ez_in']) + 1] if found_keys['ez_in'] else None,
                    table[table.index(found_keys['hd']) + 1] if found_keys['hd'] else None,
                    table[table.index(found_keys['in']) + 1] if found_keys['in'] else None,
                    table[table.index(found_keys['ez_at']) + 1]
                ]
            elif found_keys['hd_in']:
                result = [
                    table[table.index(found_keys['ez']) + 1] if found_keys['ez'] else None,
                    table[table.index(found_keys['hd_in']) + 1],
                    table[table.index(found_keys['hd_in']) + 1],
                    table[table.index(found_keys['at']) + 1] if if_at and found_keys['at'] else None
                ]
            elif found_keys['hd_at']:
                result = [
                    table[table.index(found_keys['ez']) + 1] if found_keys['ez'] else None,
                    table[table.index(found_keys['hd_at']) + 1],
                    table[table.index(found_keys['in']) + 1] if found_keys['in'] else None,
                    table[table.index(found_keys['hd_at']) + 1]
                ]
            elif found_keys['in_at']:
                result = [
                    table[table.index(found_keys['ez']) + 1] if found_keys['ez'] else None,
                    table[table.index(found_keys['hd']) + 1] if found_keys['hd'] else None,
                    table[table.index(found_keys['in_at']) + 1],
                    table[table.index(found_keys['in_at']) + 1]
                ]
            elif found_keys['ez']:
                # 默认情况
                result = table[table.index(found_keys['default']) + 1] if found_keys['default'] else None
            
            # 过滤掉None值
            return list(filter(None, result)) if isinstance(result, list) else result

        tb_lst = table.split('\n')
        tb_lst = [item for sublist in [i.split(',') for i in tb_lst] for item in sublist]
        # del all umpty elements in the list
        tb_lst = list(filter(None, tb_lst))

        # if have AT difficulty then True, if not then False
        if_at = True if tb_lst.index('Difficulty') + 1 - tb_lst.index('Level') == 4 else False
        
        difficulty = tb_lst[tb_lst.index('Difficulty') + 1 : tb_lst.index('Level')]
        level = tb_lst[tb_lst.index('Level') + 1 : tb_lst.index('Note count')]
        note_count = tb_lst[tb_lst.index('Note count') + 1 : tb_lst.index('Artist')]
        
        if 'Legacy' in difficulty:
            index = difficulty.index('Legacy')
            difficulty.pop(index)
            level.pop(index)
            note_count.pop(index)
        
        info_dict = {
            'pack' : tb_lst[tb_lst.index('Pack') + 1],
            'difficulty' : difficulty,
            'level' : level,
            'note count' : note_count,
            'artist' : tb_lst[tb_lst.index('Artist') + 1],
            'illustration' : tb_lst[tb_lst.index('Illustration') + 1],
            'duration' : tb_lst[tb_lst.index('Duration') + 1],
            'chart design' : _get_chart_design(tb_lst, if_at),
        }
        
        return info_dict
    
    def run(self, song:str) -> tuple[dict,float]:
        start_time = time.time()
        song = song.replace(' ','_')
        resp = self._fetch(f"{Config.START_URL_WIKI}{song}")
        data = self._parse_html(resp)
        table = self._get_song_data(data)
        info = self._parse_table_lst(table)
        duration = time.time() - start_time
        
        return info, duration

class MoeCrawler(Crawler):
    def __init__(self):
        super().__init__()
    
    def _get_n_parse_song_data(self, html:BeautifulSoup) -> dict:
        HTML_TAG_PATTERN = re.compile(r'<.*?>')
        _VALID_FORMAT_PATTERN = re.compile(r'^(\d+)\s+\((\d+\.\d+)\)$')
        
        def get_content(text:str) -> str:
            return HTML_TAG_PATTERN.sub('', text)

        def is_valid_format(s):
            return bool(_VALID_FORMAT_PATTERN.match(s))
        
        _lst_split = lambda lst, step: [lst[i:i+step] for i in range(0, len(lst), step)]
        
        table = html.find_all('table')

        tb_dict = {
            'main story' : table[1].find_all('td'),
            'side story' : table[2].find_all('td'),
            'ex chapter' : table[3].find_all('td'),
            'ex story' : table[4].find_all('td'),
            'single' : table[5].find_all('td')
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
            if key != 'single':
                tb_dict[key] = _lst_split(tb_dict[key],3)
            else:
                tb_dict[key] = _lst_split(tb_dict[key],4)
        
        for key in tb_dict:
            for lst in tb_dict[key]:
                if key != 'single':
                    tb_dict[key][tb_dict[key].index(lst)] = [lst[0],lst[2]]
                else:
                    tb_dict[key][tb_dict[key].index(lst)] = [lst[1],lst[3]]
        
        bpm_dict = {
            lst[0]: lst[1]
            for key in tb_dict
            for lst in tb_dict[key]
        }
        
        return bpm_dict
    
    def run(self, song:str) -> tuple[str,float]:
        start_time = time.time()
        resp = self._fetch(Config.START_URL_MOE)
        data = self._parse_html(resp)
        bpm_dict = self._get_n_parse_song_data(data)
        bpm = "175" if song == "Another Me (Neutral Moon)" else "210" if song == "Another Me (D_AAN)" else bpm_dict[song]
        duration = time.time() - start_time
        
        return bpm, duration

class PhiCrawler:
    def run(self, song:str) -> tuple[dict,float]:
        info_crawler = WikiCrawler()
        bpm_crawler = MoeCrawler()
        
        info, time_wiki = info_crawler.run(song)
        info['bpm'], time_moe = bpm_crawler.run(song)
        
        duration = time_wiki + time_moe
        
        return info, duration


if __name__ == "__main__":
    info, duration = PhiCrawler().run('Another Me (Neutral Moon)')
    print(info)
    
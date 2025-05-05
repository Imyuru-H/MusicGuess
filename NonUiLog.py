# !/.venv/Scripts python3
# -*- coding: utf-8 -*-

"""
This python module used to output logs in a given format that is eazy to differentiate.

+------------------+-----------+
| Author           : Imyuru_   |
| Version          : 0.3       |
| Last update time : 2025-3-9  |
+------------------+-----------+

"""

__version__ = 0.3

import os, datetime, platform
import colorama
from colorama import Fore, Back, Style
import psutil
import cpuinfo
import GPUtil
from prettytable import PrettyTable


colorama.init(autoreset=True)
os.system("")


class Info:
    def __init__(self):
        self.info_count = 0
        self.error_count = 0
        self.false_count = 0
        self.debug_count = 0
        self.clear_screen()
        self.get_system_info()
    
    def clear_screen(self):
        # Check OS types
        if os.name == 'nt':  # Windows
            os.system('cls')
        else:  # macOS & Linux
            os.system('clear')
    
    def get_time(self):
        time = str(datetime.datetime.now()).split(" ")[1].split(".")[0]
        return f"[{time}]"
    
    def get_system_info(self):
        # Get OS info
        os_info = platform.uname()
        
        # Get CPU info
        cpu_modle = cpuinfo.get_cpu_info()["brand_raw"]

        # Get GPU info
        cpu_count = psutil.cpu_count(logical=False)

        # Get RAM info
        memory = psutil.virtual_memory()

        # Get GPU list
        gpus = GPUtil.getGPUs()
        
        table = PrettyTable(["1","2"])
        table.add_row(["System info",f"{os_info.system} {os_info.release}"])
        table.add_row(["PC name",os_info.node])
        table.add_row(["Python version",platform.python_version()])
        table.add_row(["CPU modle",cpu_modle])
        table.add_row(["CPU count",cpu_count])
        table.add_row(["Total RAM",f"{memory.total / (1024 ** 3):.2f} GB"])
        for gpu in gpus:
            table.add_row(["GPU model",gpu.name])
            table.add_row(["GPU total VRAM",f"{gpu.memoryTotal} MB"])
        
        print(table)
    
    def info(self, text:str):
        print(f"{Style.DIM}{self.get_time()}{Style.RESET_ALL}{Fore.YELLOW}[INFO]  {Fore.RESET}{text}")
        self.info_count += 1
    
    def error(self, text:str):
        print(f"{Style.DIM}{self.get_time()}{Style.RESET_ALL}{Fore.RED}[ERROR] {Fore.RESET}{text}")
        self.info_count += 1
    
    def false(self, text:str):
        print(f"{Style.DIM}{self.get_time()}{Style.RESET_ALL}{Fore.LIGHTRED_EX}[FALSE] {Fore.RESET}{text}")
        self.info_count += 1
    
    def debug(self, text:str):
        print(f"{Style.DIM}{self.get_time()}{Style.RESET_ALL}{Fore.MAGENTA}[DEBUG] {Fore.RESET}{text}")
        self.info_count += 1
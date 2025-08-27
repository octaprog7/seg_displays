"""Вспомогательные средства для проекта seg_displays"""

import os
from collections import namedtuple

# некоторая информация о плате
board_info = namedtuple("board_info", "sysname nodename machine")

def get_board_info() -> board_info:
    """Возвращает информацию о плате"""
    s = os.uname()
    return board_info(sysname=s.sysname, nodename=s.nodename, machine=s.machine)


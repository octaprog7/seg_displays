"""Модуль для работы с индикаторами, состоящими из сегментов(!). MAX7219"""

from lib_displays.char_display_mod import CharDisplay
# from lib_displays.display_controller_mod import ICharDisplayController

'''Таблица битовых масок для основных символов для семисегментника с MAX7219.
Биты в коде символа для управления сегментами семисегментного индикатора через MAX7219 располагаются так:
    * 0-й бит (самый младший) — сегмент G   (1)
    * 1-й бит — сегмент F                   (2)
    * 2-й бит — сегмент E                   (4)
    * 3-й бит — сегмент D                   (8)
    * 4-й бит — сегмент C                   (0x10)
    * 5-й бит — сегмент B                   (0x20)
    * 6-й бит — сегмент A                   (0x40)
    * 7-й бит (старший) — сегмент DP (десятичная точка).        (0x80)

      —A—
    |     |
    F     B
    |     |
      —G—
    |     |
    E     C
    |     |
      —D—
            • DP'''

class MAX7219Display(CharDisplay):
    """Символьный дисплей, на основе MAX7219. 1..8 символов в один ряд/строку."""

    def get_segment_nbit(self, seg_name: str) -> int:
        """Возвращает номер бита, соответствующий сегменту с именем seg_name. Имя сегмента имеет длину один символ!"""
        seg_map = {'g': 0, 'f': 1, 'e': 2, 'd': 3, 'c': 4, 'b': 5, 'a': 6, 'p': 7}
        return  seg_map[seg_name]

    def init(self, value: int = 0):
        """Инициализация"""
        self.set_partial_update(True)
        self.set_inverse_logic(False)
        self.set_reverse_index(True)

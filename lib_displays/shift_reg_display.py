"""Модуль для работы с индикаторами, состоящими из сегментов на основе 74HC595 с общим катодом (активный HIGH)."""

from sensor_pack_2.base_sensor import check_value
from lib_displays.char_display_mod import CharDisplay
from lib_displays.display_controller_mod import ICharDisplayController

'''Биты в коде символа для управления сегментами семисегментного индикатора на основе 74HC595 располагаются так:

# bit 7 - segment DP
# bit 6 - segment G
# bit 5 - segment F
# bit 4 - segment E
# bit 3 - segment D
# bit 2 - segment C
# bit 1 - segment B
# bit 0 - segment A

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

class ShiftReg8Display(CharDisplay):
    """Символьный дисплей, на основе 74HC595 с общим катодом. 1..N символов в один ряд/строку."""

    def __init__(self, controller: ICharDisplayController):
        super().__init__(controller=controller)
        # для хранения пересылаемых кодов символов
        self._buf = bytearray(controller.get_columns())

    def set_buf(self, index: int, value: int) -> bytes:
        """Записывает значение value в буфер по индексу index.
        Для переопределения в классах-наследниках."""
        buf = self._buf
        buf[index] = value
        return buf

    def get_segment_nbit(self, seg_name: str) -> int:
        """Возвращает номер бита, соответствующий сегменту с именем seg_name. Имя сегмента имеет длину один символ!"""
        seg_map = {'g': 6, 'f': 5, 'e': 4, 'd': 3, 'c': 2, 'b': 1, 'a': 0, 'p': 7}
        return  seg_map[seg_name]

    def init(self, value: int = 0):
        """Инициализация"""
        self.set_inverse_logic(True)
        self.set_reverse_index(True)
        self.set_partial_update(False)
        # выводится символ, сегменты A-G-D включены, если char не может быть отображен на индикаторе!
        # self.set_non_printable('adg')

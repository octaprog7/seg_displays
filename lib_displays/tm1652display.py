"""Модуль для работы с WeAct Digital Tube Module TM1652 0.8 Inch 8.8:8.8."""

from lib_displays.display_controller_mod import ICharDisplayController
from lib_displays.char_display_mod import CharDisplay


class WADigitalTube(CharDisplay):
    """Символьный дисплей, на основе TM1652 (WeAct Digital Tube Module).
    4 символов в один ряд/строку."""

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
        self.set_inverse_logic(False)
        self.set_reverse_index(False)
        self.set_partial_update(False)

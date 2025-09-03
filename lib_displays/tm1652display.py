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

    def get_segment_nbit(self, seg_name: str) -> int:
        """Возвращает номер бита, соответствующий сегменту с именем seg_name. Имя сегмента имеет длину один символ!"""
        seg_map = {'g': 6, 'f': 5, 'e': 4, 'd': 3, 'c': 2, 'b': 1, 'a': 0, 'p': 7}
        return  seg_map[seg_name]

    def init(self, value: int = 0):
        """Инициализация"""
        self._inverse_logic = False
        # выводится символ, сегменты A-G-D включены, если char не может быть отображен на индикаторе!
        #self.set_non_printable(self.segments_to_raw('adg'))

    def show_by_pos(self, chars: str, x: int = 0, y: int = 0):
        """Выводит на дисплей коды символов из chars.
        :param chars - отображаемая на дисплее строка (4 символа максимум);
        :param x - не используется! TM1652 не имеет возможности задавать место вывода одного символа.
        :param y - не используется!
        """
        def _format(source: str, n: int) -> str:
            # Обрезаю строку до n символов
            s = source[:n]
            # Форматирую строку, длиной n, дополнением пробелами справа
            return f"{s:<{n}}"

        lc = _format(chars, self.get_columns())
        gen = CharDisplay.gen_chars_with_dp
        for cnt, char_with_dp in enumerate(gen(lc)):
            segments = self.get_segments_of_symbol(char_with_dp)
            self._buf[cnt] =  self.segments_to_raw(segments)
        # посылка готова к отправке
        self._controller.set_all(self._buf)

    def clear(self):
        self.show_by_pos(' ' * self.get_columns())
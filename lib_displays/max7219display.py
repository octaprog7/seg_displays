"""Модуль для работы с индикаторами, состоящими из сегментов(!). MAX7219"""

from lib_displays.char_display_mod import CharDisplay

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
        self._inverse_logic = False
        # выводится символ, сегменты A-G-D включены, если char не может быть отображен на индикаторе!
        #self.set_non_printable(self.segments_to_raw('adg'))

    def show_by_pos(self, chars: str, x: int = 0, y: int = 0):
        """Выводит на дисплей коды символов из chars.
        :param chars - отображаемая на дисплее строка;
        :param x - не используется, так как всего 8 знакомест!
        :param y - не используется, так как всего 8 знакомест!
        Хотите изменять положение символа, формируйте строку заранее!
        """
        buffer_len = len(chars)
        display_len = self.get_columns()
        if buffer_len > display_len:
            buffer_len = display_len

        align = self.get_alignment()
        gen = CharDisplay.gen_chars_with_dp
        val_rng = range(display_len)
        get_segments = self.get_segments_of_symbol
        seg_to_raw = self.segments_to_raw
        for cnt, char_with_dp in enumerate(gen(chars)):
            x = cnt + 1
            #       left align                         right align
            index = display_len - x if align <= 0 else buffer_len - x
            if index not in val_rng:
                break
            segments = get_segments(char_with_dp)
            symb_code = seg_to_raw(segments)
            self._controller.set_char(symb_code, index, 0)

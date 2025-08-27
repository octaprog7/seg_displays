"""Модуль для работы с индикаторами, состоящими из сегментов(!). MAX7219"""

from lib_displays.char_display_mod import CharDisplay

class MAX7219Display(CharDisplay):
    """Символьный дисплей, на основе MAX7219. 1..8 символов в один ряд/строку."""

    @staticmethod
    def ascii_to_seven_segment(char_with_dp: str, non_printable: int, inverse_logic: bool = False) -> int:
        """
        Преобразует символ или символ с десятичной точкой ('.') в битовую маску для семисегментного индикатора.
        Принимает строку длины 1 или 2, где второй символ — опциональная точка, означающая включённый сегмент DP.
        Возвращает целое число — битовую маску сегментов с учётом флага DP и возможно, инверсии логики.
        :param char_with_dp - символ или символ с десятичной точкой;
        :param non_printable - битовая маска включенных сегментов, отображаемая в случае, если набор сегментов дисплея
        не может узнаваемо отобразить символ!;
        :param inverse_logic - если Ложь, то сегмент включается 1, иначе сегмент включается 0;
        """

        if not isinstance(char_with_dp, str) or 0 == len(char_with_dp) or len(char_with_dp) > 2:
            raise ValueError("Ожидается строка длиной 1 или 2.")

        if not non_printable in range(0x100): # для семи (восьми, если учесть десятичную точку) сегментов достаточно одного байта!
            raise ValueError(f"Неверное значение параметра non_printable: {non_printable}!")

        two_char = 2 == len(char_with_dp)
        # Обработка случая: символ + точка (например, 'A.')
        if two_char and '.' != char_with_dp[1]:
                raise ValueError("Если длина равна 2 символам, то вторым символом должна быть '.', десятичная точка!")
        char = char_with_dp[0]
        decimal_point = two_char

        '''Таблица битовых масок для основных символов для семисегментника с MAX7219.
        Биты в коде символа для управления сегментами семисегментного индикатора через MAX7219 располагаются так:
            * 0-й бит (самый младший) — сегмент G
            * 1-й бит — сегмент F 
            * 2-й бит — сегмент E 
            * 3-й бит — сегмент D 
            * 4-й бит — сегмент C 
            * 5-й бит — сегмент B 
            * 6-й бит — сегмент A 
            * 7-й бит (старший) — сегмент DP (десятичная точка).

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
        # постоянные приведены в ПРЯМОЙ логике, то есть 1 - включить сегмент, 0 - выключить сегмент!
        # 7 bit - H (DP); 6 bit - A; 5 bit - B; 4 bit - C; 3 bit - D; 2 bit - E; 1 bit - F; 0 bit - G;
        digits_segment_map = (
                0b0111_1110,  # 0
                0b0011_0000,  # 1 B C
                0b0110_1101,  # 2 A B G E D
                0b0111_1001,  # 3 A B G C D
                0b0011_0011,  # 4
                0b0101_1011,  # 5
                0b0101_1111,  # 6
                0b0111_0000,  # 7
                0b0111_1111,  # 8
                0b0111_1011,  # 9
            )
        segment_map_letters = {
                'A': 0b0111_0111,
                'b': 0b0001_1111,
                'C': 0b0100_1110,
                'd': 0b0011_1101,
                'E': 0b0100_1111,
                'F': 0b0100_0111,
                'H': 0b0011_0111,
                'I': 0b0011_0000,
                'J': 0b0011_1100,
                'L': 0b0000_1110,
                'n': 0b0001_0101,
                'o': 0b0001_1101,
                'P': 0b0110_0111,
                'S': 0b0101_1011,
                'U': 0b0011_1110,
                'X': 0b0011_0111, # X как H. А как вы думали? Забудьте про двоеточие, кавычки и много еще что.
                '-': 0b0000_0001,
                '.': 0b1000_0000,
                '_': 0b0000_1000,
                '=': 0b0000_1001,
                ' ': 0b0000_0000,
                '|': 0b0000_0110,
                '[': 0b0100_1110,
                ']': 0b0111_1000,
                '?': 0b0110_0101,
                '°': 0b0110_0011,  # попытка отобразись символ градуса на скудных семи сегментах
        }   # segment_map_letters = {

        ascii_code = ord(char)
        if ascii_code in range(0x30, 0x3A):  # '0'..'9'
            code = digits_segment_map[ascii_code - 0x30]
        else:   # все остальное, кроме цифр
            code = segment_map_letters.get(char, non_printable)

        if decimal_point:
            code |= 0b10000000  # добавляю десятичную точку

        if inverse_logic:
            code = 0xFF & (~code)  # инверсия бит
        return code

    def init(self, value: int = 0):
        """Инициализация"""
        self._inverse_logic = False
        # выводится символ, сегменты A-G-D включены, если char не может быть отображен на индикаторе!
        self.set_non_printable(0b0100_1001)

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
        inv_logic = self.is_inverse_logic()
        gen = CharDisplay.gen_chars_with_dp
        ascii_to_7seg = MAX7219Display.ascii_to_seven_segment
        np_char = self.get_non_printable()
        for cnt, _data in enumerate(gen(chars)):
            x = cnt + 1
            #       left align                         right align
            index = display_len - x if align <= 0 else buffer_len - x
            if index < 0 or index >= display_len:
                break

            symb_code = ascii_to_7seg(_data, np_char, inv_logic)
            self._controller.set_char(symb_code, index, 0)

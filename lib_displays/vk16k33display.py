"""Модуль для работы с индикаторами, состоящими из сегментов(!). VK16K33, HT1621"""

lang = 'en'

from lib_displays.char_display_mod import CharDisplay
#from sensor_pack_2.base_sensor import check_value

_lang_dict = None

if 'en' == lang:
    from lib_displays.en_lang_14_seg import eng_to_14segments
    _lang_dict = eng_to_14segments
if 'ru' == lang:
    from lib_displays.ru_lang_14_seg import ru_to_14segments
    _lang_dict = ru_to_14segments


class VK16K33Display(CharDisplay):
    """Символьный дисплей, на основе VK16K33. 4 символа в один ряд/строку."""

    # имена сегментов 14-ти сегментного индикатора. 1-g1, 2-g2
    # имена сегментов расположены в порядке их расположения в бейте результата.
    # например, имя сегмента 'a' находится в позиции 0, строки valid_seg_names, что дает значение 2^0 = 1
    # например, имя сегмента 'd' находится в позиции 3, строки valid_seg_names, что дает значение 2^3 = 8
    # например, имя сегмента '2'-g2 находится в позиции 7, строки valid_seg_names, что дает значение 2^7 = 128
    # сегменты "abcdef12" образуют младший байт, сегменты "hijmlk" образуют старший байт значения.
    # p имя сегмента десятичной точки
    _valid_seg_names = "abcdef12hijmlkp"
    _seg_index_map = {c: i for i, c in enumerate(_valid_seg_names)}

    @staticmethod
    def segments_to_raw(segments_on: str, dp: bool = False) -> int:
        """
        Преобразует имена включенных сегментов 14-ти сегментного индикатора в двухбайтное число для записи по адресу символа индикатора.
        :param segments_on - Строка с правильными именами (смотри valid_seg_names) сегментов 14-ти сегментного индикатора, которые должны быть включены!
        :param dp - Десятичная точка, включена если Истина.
        :return: Двух байтное значение для записи по адресу символа 14-ти сегментного индикатора!
        """
        ret_val = 0
        index_map = VK16K33Display._seg_index_map
        for segm_name in segments_on:
            seg_index = index_map[segm_name]
            ret_val |= 1 << seg_index
        if dp:
            ret_val |= 0b0100_0000_0000_0000
        return ret_val

    @staticmethod
    def ascii_to_14_seg(char_with_dp: str, non_printable: int, lang_dict: dict = _lang_dict) -> int:
        """По коду символа char_with_dp возвращает код сегментов 14-ти сегментного знакоместа.
        :param char_with_dp: Строка из одного или двух символов. Первый символ выводится на дисплее, Второй символ должен быть точкой, если он есть!
        :param non_printable: Сырое значение для символа-замены тех, которых невозможно узнаваемо напечатать.
        :param lang_dict: Словарь символов: символ -> строка включённых сегментов
        :return: Двух байтное значение для записи по адресу символа 14-ти сегментного индикатора!
        """

        # содержит общие символы
        common_numbers_symbols = {
            # Цифры 0 - 9
            '0': "abcdefjm",
            '1': "bcj",
            '2': "ab2md",
            '3': "abcd2",
            '4': "f12bc",
            '5': "af12cd",
            '6': "acdef12",
            '7': "ajm12",
            '8': "abcdef12",
            '9': "abcdf12",
        }

        spec_symbols = {
            # спецсимволы и знаки препинания!
            '.': "p",
            ' ': "",
            '+': "12il",
            '-': "12",
            '_': "d",
            '=': "12d",
            '|': "fe",
            '/': "mj",
            '\\': "hk",
            '?': "12abe",
            '[': "adef",
            ']': "abcd",
            '(': "jk",
            ')': "hm",
            '$': "af12cdil",
            '%': "mj1fh2cl",
            '^': "fh",
            '°' : "ahj" # попытка отобразись символ градуса
        } # spec_symbols = {

        if not isinstance(char_with_dp, str) or 0 == len(char_with_dp) or len(char_with_dp) > 2:
            raise ValueError("Ожидается строка длиной 1 или 2.")

        if not non_printable in range(0xFFFF): # двух байтное значение
            raise ValueError(f"Неверное значение параметра non_printable: {non_printable}!")

        two_char = 2 == len(char_with_dp)
        # Обработка случая: символ + точка (например, 'A.')
        if two_char and '.' != char_with_dp[1]:
            raise ValueError("Если длина равна 2 символам, то вторым символом должна быть '.', десятичная точка!")
        char = char_with_dp[0]
        decimal_point = two_char

        if char.isdigit():  # цифра 0..9
            return VK16K33Display.segments_to_raw(common_numbers_symbols[char], decimal_point)

        segments = spec_symbols.get(char)
        if not segments is None:
            return VK16K33Display.segments_to_raw(segments, decimal_point)

        segments = lang_dict.get(char, non_printable)
        if non_printable == segments:
            # символа нет в словаре, увы!
            if char.isalpha():
                # это буквенный символ, меняю строчную на прописную в попытке вернуть хоть что-то,
                # кроме non_printable!
                same_char = char.upper() if char.islower() else char
                segments = lang_dict.get(same_char, None)
                if segments is None:
                    return non_printable  # не фартануло!
                # похожий символ найден, возврат соответствующих ему, включенных сегментов
                return VK16K33Display.segments_to_raw(segments, decimal_point)
            return non_printable
        # символ найден, возврат соответствующих ему, включенных сегментов
        return VK16K33Display.segments_to_raw(segments, decimal_point)

    def show_by_pos(self, chars: str, x: int = 0, y: int = 0):
        """Выводит на дисплей коды символов из chars.
        :param chars - строка для отображения;
        :param x - индекс знакоместа, с которого начинается отображение первого символа chars;
        :param y - не используется, так как всего 8 знакомест;
        Хотите изменять положение символа, формируйте строку заранее!"""
        gen = CharDisplay.gen_chars_with_dp
        cols = self.get_columns()
        ascii_to_seg = VK16K33Display.ascii_to_14_seg
        np_char = self.get_non_printable()
        for cnt, char_with_dp in enumerate(gen(chars)):
            pos = x + cnt
            if pos < 0 or pos >= cols:
                break
            symb_code = ascii_to_seg(char_with_dp, np_char)
            self._controller.set_char(symb_code, pos, 0)

    def init(self, value: int = 0):
        """Инициализация"""
        self.set_non_printable(0x3808)
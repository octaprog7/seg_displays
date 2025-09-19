"""Модуль для работы с индикаторами, состоящими из сегментов(!). VK16K33, HT1621"""
from lib_displays.display_controller_mod import ICharDisplayController
from lib_displays.char_display_mod import CharDisplay


class VK16K33Display(CharDisplay):
    """Символьный дисплей, на основе VK16K33. 4 символа в один ряд/строку."""

    # Имена сегментов 14-ти сегментного индикатора. 1-g1, 2-g2.
    # Имена сегментов расположены в порядке их расположения в бейте результата.
    # Например, имя сегмента 'a' находится в позиции 0, строки valid_seg_names, что дает значение 2^0 = 1.
    # Например, имя сегмента 'd' находится в позиции 3, строки valid_seg_names, что дает значение 2^3 = 8.
    # Например, имя сегмента '2'-g2 находится в позиции 7, строки valid_seg_names, что дает значение 2^7 = 128.
    # Сегменты "abcdef12" образуют младший байт, сегменты "hijmlk" образуют старший байт значения.
    # p имя сегмента десятичной точки
    _valid_seg_names = "abcdef12hijmlkp"
    _seg_values_map = {c: i for i, c in enumerate(_valid_seg_names)}

    def __init__(self, controller: ICharDisplayController, alpha_letters: dict):
        """

        :param controller: ссылка на класс, контроллер дисплея
        :param alpha_letters: ссылка на словарь соответствия букв алфавита и сегментов, отображающих эту букву
        """
        if not isinstance(alpha_letters, dict):
            raise ValueError(f"Неверный тип alpha_letters")

        super().__init__(controller=controller)
        # словарь хранит соответствия буквы алфавита и сегментов, ее отображающих
        self._alpha_letters = alpha_letters

    def get_segment_nbit(self, seg_name: str) -> int:
        """Возвращает номер бита, соответствующий сегменту с именем seg_name. Имя сегмента имеет длину один символ!"""
        return  VK16K33Display._seg_values_map[seg_name]

    def get_segments_of_symbol(self, char_with_dp: str) -> str:
        # содержит общие символы
        seg_map_digits = {
            # Цифры 0 - 9
            '0': "abcdefjm",
            '1': "bcj",
            '2': "ab2md",
            '3': "abcd2",
            '4': "f12bc",
            '5': "ah2cd",
            '6': "acdef12",
            '7': "ajm12",
            '8': "abcdef12",
            '9': "abcdf12",
        }
        dp_seg_name = 'p'

        segment_map_letters =self._alpha_letters

        spec_symbols = {
            # спецсимволы и знаки препинания!
            '.': dp_seg_name,
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
            '°': "ahj"  # попытка отобразись символ градуса
        }  # spec_symbols = {

        if not isinstance(char_with_dp, str) or 0 == len(char_with_dp) or len(char_with_dp) > 2:
            raise ValueError("Ожидается строка длиной 1 или 2.")

        two_char = 2 == len(char_with_dp)
        # Обработка случая: символ + точка (например, 'A.')
        if two_char and '.' != char_with_dp[1]:
            raise ValueError("Если длина равна 2 символам, то вторым символом должна быть '.', десятичная точка!")
        char = char_with_dp[0]
        #decimal_point = two_char

        if char.isdigit():  # цифра 0..9
            return seg_map_digits.get(char, self.get_non_printable())

        if char.isalpha():  # буквы
            return segment_map_letters.get(char, self.get_non_printable())
        # все остальные символы
        return spec_symbols.get(char, self.get_non_printable())

    def init(self, value: int = 0):
        """Инициализация"""
        self.set_non_printable('12ad')
        self.set_inverse_logic(False)
        self.set_reverse_index(False)
        self.set_partial_update(True)
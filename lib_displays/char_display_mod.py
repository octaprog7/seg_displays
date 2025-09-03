from collections import namedtuple
from lib_displays.display_controller_mod import ICharDisplayController
from sensor_pack_2.base_sensor import check_value
import micropython

# свойства символьного дисплея
base_display_prop = namedtuple("base_display_prop", "columns rows")
# прямоугольная область
rect_area = namedtuple("rect_area", "x0 y0 x1 y1")

'''
Расположение сегментов 7-сегментного дисплея, управляемого микросхемой TM1652,
в текстовом виде с именами сегментов выглядит так:
     --a--
    |     |
   f|     |b
    |--g--|
   e|     |c
    |     |
     --d--   .dp (точка)
Бит 	Назначение сегмента                 Значение
0 	Сегмент a (верхний горизонтальный)      зависит от производителя
1 	Сегмент b (верхний правый вертикальный) зависит от производителя
2 	Сегмент c (нижний правый вертикальный)  зависит от производителя
3 	Сегмент d (нижний горизонтальный)       зависит от производителя
4 	Сегмент e (нижний левый вертикальный)   зависит от производителя
5 	Сегмент f (верхний левый вертикальный)  зависит от производителя
6 	Сегмент g (средний горизонтальный)      зависит от производителя
7 	Десятичная точка (dp)                   зависит от производителя
'''


class BaseCharDisplay:
    """Основа для всех представлений символьных дисплеев"""

    def __init__(self, controller: ICharDisplayController):
        """
        :param controller - контроллер дисплея(чип).
        """
        self._controller = controller
        self._cols = controller.get_columns()
        self._rows = controller.get_rows()
        # сегменты символа, заменяющие собой символ,
        # который невозможно узнаваемо(!) напечатать в знакоместе.
        self._np_seg_names = 'adg'
        # если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!
        self._inverse_logic = False

    def is_inverse_logic(self) -> bool:
        """если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!"""
        return self._inverse_logic

    def set_inverse_logic(self, value: bool):
        """если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!"""
        self._inverse_logic = value

    def set_non_printable(self, seg_names: str):
        """Устанавливает сырое значение сегментов символа, заменяющий собой символ,
        который невозможно узнаваемо(!) напечатать в знакоместе."""
        self._np_seg_names = seg_names

    def get_non_printable(self) -> str:
        """Возвращает сырое значение сегментов символа, заменяющий собой символ,
        который невозможно узнаваемо(!) напечатать в знакоместе."""
        return self._np_seg_names

    def get_columns(self) -> int:
        """Возвращает кол-во столбцов дисплея."""
        return self._cols

    def get_rows(self) -> int:
        """Возвращает кол-во строк дисплея."""
        return self._rows

    def init(self, value: int = 0):
        """Выполняет аппаратную и программную инициализацию."""
        raise NotImplemented

    def test(self, value: bool):
        """ВКлючает (если value Истина) встроенный тест дисплея.
        ВЫключает (если value Ложь) встроенный тест дисплея"""
        raise NotImplemented

    def get_display_prop(self) -> base_display_prop:
        """Возвращает основные свойства дисплея"""
        return base_display_prop(columns=self.get_columns(), rows=self.get_rows())

    def set_alignment(self, value: int = -1):
        """Устанавливает выравнивание для вывода строки.
        alignment - выравнивание. -1 - по левому краю; 0 - по центру; 1 - по правому краю."""
        raise NotImplemented

    def show_by_pos(self, chars: str, x: int, y: int):
        """Отображает символы из строки chars.
        :param chars - отображаемая на дисплее строка;
        :param x - позиция первого символа по горизонтали.
        :param y - позиция первого символа по вертикали."""
        raise NotImplementedError

    def show_by_rect(self, info: str, area: rect_area):
        """Отображает символы из строки info в прямоугольной области area."""
        raise NotImplementedError

    def clear(self):
        """Очищает весь дисплей от символов"""
        s = " " * self.get_columns()
        # построчная очистка
        for n_row in range(self.get_rows()):
            self.show_by_pos(s, 0, n_row)

# символы, которые можно считать однозначно и чётко отображаемыми на семисегментном индикаторе:
# Цифры (0-9):
# 0, 1, 2, 3, 4, 5, 6, 7, 8, 9
# Буквы (в основном заглавные или упрощённые строчные, читаемые однозначно):
# A, b, C, d, E, F, G, H, I, J, L, n, o, P, U
# Другие символы: дефис ("-"), иногда точка (DP) для десятичных чисел


class CharDisplay(BaseCharDisplay):
    """Символьный дисплей"""

    @staticmethod
    @micropython.viper
    def _get_power_of_two(n: int) -> int:
        """Возвращает n-ную степень числа два, где n >= 0."""
        return 1 << n

    @staticmethod
    def gen_chars_with_dp(input_str: str) -> str:
        """Генератор, который перебирает строку символов input_str и выдаёт по одному элементу — либо одиночный символ,
        либо символ с десятичной точкой (DP) в виде объединённой строки длиной 2 (например 'А.').

        Каждый элемент соответствует одному знаку для семисегментного индикатора с учётом десятичной точки.

        Алгоритм:
            - Последовательно принимает символы из входной строки.
            - Собирает символы в буфер по два.
            - Если второй символ — точка '.', объединяет её с первым символом и выдаёт как один элемент (например, 'A.').
            - Если второй символ не точка, то выдаёт первый символ отдельно.
            - Если первый символ — одиночная точка '.', она тоже выдаётся как отдельный элемент.
            - В конце, если остался непереданный символ, он тоже отдаётся.

        Использование:
            - Помогает разбить строку с условным указанием десятичной точки в виде символа '.' сразу после основного символа.
            - Результат удобно передавать в функцию преобразования символов в коды для семисегментных индикаторов, учитывающих DP.

        Аргументы:
            input_string (str): Входная строка с символами и, опционально, десятичными точками, указанными как '.' после символа.

        Результат:
            Итератор[str]: Последовательность строк длиной 1 (символ без DP) или 2 (символ+'.' для DP)."""

        buffer = ['', '']  # массив из двух символов
        count = 0  # счётчик заполненных позиций (0 или 1)
        decimal_point = '.'

        for ch in input_str:
            buffer[count] = ch
            count += 1

            if count == 2:
                if buffer[1] == decimal_point:
                    yield buffer[0] + buffer[1]
                    count = 0
                else:
                    if buffer[0] == decimal_point:
                        yield decimal_point
                    else:
                        yield buffer[0]
                    buffer[0] = buffer[1]
                    count = 1

        # После цикла проверяем, остался ли символ в буфере (count == 1)
        if 1 == count:
            yield buffer[0]

    def __init__(self, controller: ICharDisplayController):
        """Инициализация"""
        super().__init__(controller=controller)
        self._alignment = -1

    def get_segment_nbit(self, seg_name: str) -> int:
        """Возвращает номер бита, соответствующий сегменту с именем seg_name. Имя сегмента имеет длину один символ!
        Для переопределения в классах-наследниках!"""
        raise NotImplemented

    @micropython.native
    def _get_segment_value(self, seg_name) -> int:
        """Возвращает значение сегмента в байте/слове данных."""
        return CharDisplay._get_power_of_two(self.get_segment_nbit(seg_name))

    @micropython.native
    def segments_to_raw(self, segments_on: str) -> int:
        """
        Преобразует имена включенных сегментов 7/14-ти сегментного индикатора в одно или двухбайтное число для записи по адресу символа индикатора.
        :param segments_on - Строка с правильными именами сегментов 7/14-ти сегментного индикатора, которые должны быть включены!
        :param dp - Десятичная точка, включить, если Истина.
        :return: Значение для записи по адресу символа 7/14-ти сегментного индикатора!
        """
        ret_val = 0
        for segm_name in segments_on:
            ret_val |= self._get_segment_value(segm_name)
        return ret_val

    def get_segments_of_symbol(self, char_with_dp: str) -> str:
            """Возвращает строку из имен сегментов, которые должны быть включены для отображения символа char.
            :param char_with_dp - строка длиной один или два символа. если есть второй символ, то им должна быть десятичная точка!
            :return: строка из имен сегментов, которые должны быть включены для отображения символа char или значение типа int,
            что означает, что символ не отображается этим дисплеем!
            Для переопределения в классах-наследниках.
            """
            dp_seg_name = 'p'
            # содержит все цифры и их сегменты. Цифры 0 - 9
            seg_map_digits = {
                '0': "abcdef",
                '1': "bc",
                '2': "abged",
                '3': "abgcd",
                '4': "fgbc",
                '5': "afgcd",
                '6': "afgcde",
                '7': "abc",
                '8': "abcdefg",
                '9': "abcdfg",
            }
            # содержит все отображаемые буквы и некоторые другие символы
            segment_map_letters = {
                'A': 'abcefg',
                'b': 'cdefg',
                'C': 'adef',
                'c': 'deg',
                'd': 'bcdeg',
                'E': 'agdef',
                'F': 'aefg',
                'G': 'acdef',
                'H': 'bcefg',
                'J': 'bcd',
                'L': 'def',
                'n': 'ceg',
                'o': 'cdeg',
                'r': 'eg',
                'P': 'abefg',
                'U': 'bcdef',
                '-': 'g',
                '.': dp_seg_name,  # сегмент DP - десятичная точка
                '_': 'd',
                '=': 'gd',
                ' ': '',
                '|': 'ef',
                '[': 'defa',
                ']': 'abcd',
                '°': 'abgf',  # попытка отобразись символ градуса на скудных семи сегментах
            }  # segment_map_letters = {

            if not isinstance(char_with_dp, str) or 0 == len(char_with_dp) or len(char_with_dp) > 2:
                raise ValueError("Ожидается строка длиной 1 или 2.")

            two_char = 2 == len(char_with_dp)
            # Обработка случая: символ + точка (например, 'A.')
            if two_char and '.' != char_with_dp[1]:
                raise ValueError("Если длина равна 2 символам, то вторым символом должна быть '.', десятичная точка!")
            char = char_with_dp[0]
            decimal_point = two_char
            #
            _map = seg_map_digits if char.isdigit() else segment_map_letters
            retval = _map.get(char, self.get_non_printable())
            if decimal_point:
                retval = retval + dp_seg_name  # добавляю десятичную точку
            return retval

    def set_alignment(self, value: int = -1):
        """Устанавливает выравнивание при выводе текста.
        :param value - выравнивание. -1 - по левому краю; 0 - по центру; 1 - по правому краю"""
        check_value(value, range(-1, 2), f"Неверное значение выравнивания: {value}.")
        self._alignment = value

    def get_alignment(self) -> int:
        """Возвращает выравнивание."""
        return self._alignment

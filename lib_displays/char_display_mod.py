from collections import namedtuple
from lib_displays.display_controller_mod import ICharDisplayController
from sensor_pack_2.base_sensor import check_value

# свойства символьного дисплея
base_display_prop = namedtuple("base_display_prop", "columns rows")
# прямоугольная область
rect_area = namedtuple("rect_area", "x0 y0 x1 y1")

class BaseCharDisplay:
    """Основа для всех представлений символьных дисплеев"""

    def __init__(self, controller: ICharDisplayController):
        """
        :param controller - контроллер дисплея(чип).
        """
        self._controller = controller
        self._cols = controller.get_columns()
        self._rows = controller.get_rows()
        # сырое значение сегментов символа, заменяет собой символ,
        # который невозможно узнаваемо(!) напечатать в знакоместе.
        self._non_printable = 0xFF
        # если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!
        self._inverse_logic = False

    def is_inverse_logic(self) -> bool:
        """если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!"""
        return self._inverse_logic

    def set_inverse_logic(self, value: bool):
        """если Ложь, то сегмент включается единицей, иначе сегмент включается нулем!"""
        self._inverse_logic = value

    def set_non_printable(self, raw_value: int):
        """Устанавливает сырое значение сегментов символа, заменяющий собой символ,
        который невозможно узнаваемо(!) напечатать в знакоместе."""
        self._non_printable = raw_value

    def get_non_printable(self) -> int:
        """Возвращает сырое значение сегментов символа, заменяющий собой символ,
        который невозможно узнаваемо(!) напечатать в знакоместе."""
        return self._non_printable

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
# A, b, C, d, E, F, H, I, J, L, n, o, P, S, U
# Другие символы: дефис ("-"), иногда точка (DP) для десятичных чисел


class CharDisplay(BaseCharDisplay):
    """Символьный дисплей"""
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

    def set_alignment(self, value: int = -1):
        """Устанавливает выравнивание при выводе текста.
        :param value - выравнивание. -1 - по левому краю; 0 - по центру; 1 - по правому краю"""
        check_value(value, range(-1, 2), f"Неверное значение выравнивания: {value}.")
        self._alignment = value

    def get_alignment(self) -> int:
        """Возвращает выравнивание."""
        return self._alignment

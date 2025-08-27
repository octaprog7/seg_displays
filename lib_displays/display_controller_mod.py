"""Содержит интерфейсы контроллера дисплея"""

class IDisplayController:
    """Основа для всех контроллеров дисплея."""

    def set_brightness(self, value: int):
        """Устанавливает яркость всех элементов одновременно."""
        raise NotImplemented

    def set_display_test(self, value: bool):
        """Если value в Истина, то дисплей переводится в режим проверки с включением всех элементов!"""
        raise NotImplemented

    def set_shutdown(self, value: bool):
        """Если value в Истина, то дисплей переводится в режим shutdown/выключено"""
        raise NotImplemented

    def init(self, columns: int, rows: int, value: int = 0):
        """Производит аппаратную инициализацию. value определяет тип инициализации."""
        raise NotImplemented

    def get_columns(self) ->int:
        """Возвращает количество столбцов элементов дисплея"""
        raise NotImplemented

    def get_rows(self) -> int:
        """Возвращает количество строк элементов дисплея"""
        raise NotImplemented



class ICharDisplayController(IDisplayController):
    """Методы контроллера простейшего символьного дисплея."""

    def set_char(self, char_code: int, x: int, y: int):
        """char_code - код, соответствующий отображению определенного символа. x, y - вертикальная и горизонтальная
        координаты символа в системе координат дисплея. Эта система координат может быть какой угодно!
        Преобразованием этих координат в координаты, позволяющие видеть изображение в привычном виде,
        контроллер дисплея НЕ ЗАНИМАЕТСЯ!"""
        raise NotImplemented

    def set_brightness(self, value: int):
        """Устанавливает яркость всех элементов одновременно."""
        raise NotImplemented

    # IDisplayController
    def set_shutdown(self, value: bool):
        """Если value в Истина, то дисплей переводится в режим shutdown/выключено"""
        raise NotImplemented

    # IDisplayController
    def set_display_test(self, value: bool):
        """Если value в Истина, то дисплей переводится в режим проверки с включением всех элементов!
        Внимание! В режиме проверки дисплея (все сегменты включены) до тех пор, пока регистр проверки дисплея не будет
        перенастроен для нормальной работы!"""
        raise NotImplemented


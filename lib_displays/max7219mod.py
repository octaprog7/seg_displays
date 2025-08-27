"""
MicroPython SPI MAXx7219 LED matrix driver
"""

# micropython
# MIT license

from machine import Pin
from micropython import const
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, check_value
from lib_displays.display_controller_mod import ICharDisplayController


class MAX7219(ICharDisplayController):
    """Программное представление MAX7219. Контроллер группы семисегментных индикаторов."""

    # адреса регистров
    cmd_nop = const(0)          # нет операции
    cmd_digit_0 = const(1)      # знакоместо 1. 1 - знакоместо 1, 2- знакоместо 2, ... 8 - знакоместо 8
    cmd_decode_mode = const(9)  # включение/отключение режима декодирования
    cmd_intensity = const(10)   # яркость (для всех знакомест)
    cmd_scan_limit = const(11)  # предел сканирования. устанавливает количество отображаемых цифр, от 1 до 8.
    cmd_shutdown = const(12)    # включение/отключение дисплея
    cmd_display_test = const(15)    # включение/отключение режима проверки дисплея

    def __init__(self, adapter: bus_service.SpiAdapter, chip_select: Pin):
        """
        :param adapter - адаптер шины.
        :param chip_select - вывод МК, управляющий выводом выбора чипа/микросхемы."""
        self._connector = DeviceEx(adapter=adapter, address=chip_select, big_byte_order=True)
        self._cs = chip_select
        # количество знакомест дисплея в ширину
        self._columns = None
        # количество знакомест дисплея в высоту
        self._rows = None
        # для пересылки по шине
        self._packet = bytearray(2)

    def _setup_bus(self):
        """Настройки для правильной передачи данных по шине."""
        _conn = self._connector
        _conn.use_data_mode_pin = False

    def _write(self, buf: bytes, setup_bus: bool = False):
        """Запись сырых данных по шине адресату.
        :param buf - массив данных для передачи по шине.
        :param setup_bus - адаптер могут использовать несколько(!) устройств на шине, поэтому, иногда,
        перед каждой записью в шину необходима её настройка!"""
        if setup_bus:
            self._setup_bus()
        self._cs(0)
        self._connector.write(buf)
        self._cs(1)

    def send_cmd(self, command: int, value: int):
        """Пересылает пакет данных устройству по шине."""
        valid_rng = range(16)
        check_value(command, valid_rng, f"Код 0x{value:x} команды вне диапазона {valid_rng}!")
        _p = self._packet
        _p[0], _p[1] = command, value
        self._write(_p)

    # IDisplayController
    def get_columns(self) ->int:
        """Возвращает кол-во столбцов элементов дисплея."""
        return self._columns

    # IDisplayController
    def get_rows(self) ->int:
        """Возвращает кол-во строк элементов дисплея."""
        return self._rows

    # IDisplayController
    def set_char(self, code: int, x: int, y: int):
        """
        :param code - код, соответствующий отображению определенного символа на семисегментном индикаторе;
        :param x - индекс положения, определяющий положение символа. 0..количество_столбцов-1;
        :param y - индекс положения, определяющий положение символа. 0..строк-1;"""
        check_value(x, range(self.get_columns()), f"Неверная позиция символа с кодом 0x{code:x}")
        self.send_cmd(MAX7219.cmd_digit_0 + x, code)

    # IDisplayController
    def set_brightness(self, value: int):
        """Устанавливает яркость всех знакомест одновременно.
        :param value Значение в диапазоне 0..15"""
        check_value(value, range(16), f"Яркость вне диапазона: {value}")
        self.send_cmd(MAX7219.cmd_intensity, value)

    # IDisplayController
    def _set_scan_limit(self, value: int):
        """Устанавливает количеством семисегментных (или светодиодных) индикаторов, которые обновляются микросхемой.
        Указывает, сколько из подключённых индикаторов следует отображать и обновлять. Определяет максимальный индекс активного индикатора."""
        check_value(value, range(1, 9), f"Превышен предел сканирования: {value}")
        self.send_cmd(MAX7219.cmd_scan_limit, value)

    # IDisplayController
    def set_shutdown(self, value: bool):
        """Включает/отключает дисплей.
        :param value Если Истина, то дисплей переводится в режим shutdown/выключено."""
        self.send_cmd(MAX7219.cmd_shutdown, int(not value))

    # IDisplayController
    def set_display_test(self, value: bool):
        """Если value Истина, то дисплей переводится в режим проверки с включением всех сегментов!
        Внимание! В режиме проверки дисплея (все сегменты включены) до тех пор, пока регистр проверки дисплея не будет
        перенастроен для нормальной работы!"""
        self.send_cmd(MAX7219.cmd_display_test, 1 if value else 0)

    def set_decode(self, decode_bits: int):
        """Устанавливает режим декодирования знакоместа!
        Если в бите номер 0, decode_bits, установлена 1, то нулевое знакоместо декодируется B - кодом. Иначе декодирование отключено!
        Если в бите номер 1, decode_bits, установлена 1, то первое знакоместо декодируется B - кодом. Иначе декодирование отключено!
        ...
        Если в бите номер 7, decode_bits, установлена 1, то седьмое знакоместо декодируется B - кодом. Иначе декодирование отключено!
        """
        check_value(decode_bits, range(0x100), f"Значение вне диапазона: {decode_bits}")
        self.send_cmd(MAX7219.cmd_decode_mode, int(decode_bits))

    # IDisplayController
    def init(self, columns: int = 8, rows: int = 1, value: int = 0):
        """Первоначальная настройка дисплея. Вызывать сразу после конструктора!"""
        if columns <= 0 or rows <= 0:
            raise ValueError(f"Неверное значение строк: {rows} или столбцов: {columns}!")
        self._columns = columns
        self._rows = columns
        #
        self.set_shutdown(True) # ВЫКлючаю дисплей
        self.set_decode(0x00)   # отключаю В-код
        self._set_scan_limit(self.get_columns() - 1)
        self.set_display_test(False)
        self.set_shutdown(False)    # ВКлючаю дисплей


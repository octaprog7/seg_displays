"""
MicroPython I2C VK16K33 LED matrix driver
"""

# micropython
# MIT license

#from machine import Pin
from micropython import const
from sensor_pack_2 import bus_service
from sensor_pack_2.base_sensor import DeviceEx, check_value
from lib_displays.display_controller_mod import ICharDisplayController

class VK16K33(ICharDisplayController):
    """Представление VK16K33. Предназначен для управления LED-матрицами и семисегментными дисплеями,
    поддерживает до 16×8 сегментов (128 светодиодов)."""
    cmd_system_setup = const(0x20)  # бит 0 (S) в 1, осциллятор дисплея включен, иначе выключен
    cmd_set_brightness = const(0xE0)  # в младших четырех битах находится яркость: 0-15
    # бит 0 управляет включением дисплея (1 - включен);
    # биты 1 и 2 управляют частотой мигания дисплея: 0 - мигание выключено,
    # 1 - мигание со скоростью 2 Гц; 2 - мигание со скоростью 1 Гц, 3 - мигание со скоростью 1/2 Гц
    cmd_display_setup = const(0x80)



    def __init__(self, adapter: bus_service.I2cAdapter, address: int = 0x70, big_byte_order: bool = False):
        """
        :param adapter - адаптер шины,
        :param address - адрес на шине,
        :param big_byte_order - порядок следования байт в слове.
        big_byte_order должно быть в True для VK16K33(!); у HT16K33 обычно little endian(!) порядок байт!
        """
        self._connector = DeviceEx(adapter=adapter, address=address, big_byte_order=big_byte_order)
        # для передачи позиции и кода символа в дисплей
        self._packet = bytearray(3)
        # количество знакомест дисплея в ширину
        self._columns = None
        # количество знакомест дисплея в высоту
        self._rows = None
        # текущая частота мигания дисплея
        self._blink_freq = None
        # Если Истина, то дисплей включен
        self._display_on = None
        # Если Истина, то осциллятор ВЫключен и дисплей НЕ работает (режим сна)!
        self._standby = None

    def _write(self, buf: bytes):
        """Запись в регистр VK16K33 с адресом addr значения value."""
        if isinstance(buf, (bytes, bytearray)):
            self._connector.write(buf)

    def _set_standby(self, value: bool):
        """
        Включает или выключает режим standby.
        value в True - включить standby (бит S=0, осциллятор выключен)
        enable = False - выйти из standby (бит S=1, осциллятор включен)
        """
        # бит 0x01 - бит S (0 - standby, 1 - normal)
        cmd = VK16K33.cmd_system_setup | (0x00 if value else 0x01)
        # Передача команды
        self._write(bytes((cmd,)))
        self._standby = value

    def set_char(self, char_code: int, x: int, y: int = 0):
        """
        Выводит один символ в 14-сегментном знакоместе дисплея, управляемом VK16K33.
        :param char_code: 16-битный код сегментов символа
        :param x: позиция символа (0..3)
        :param y: позиция символа по вертикали. Не используется!
        """
        valid_rng = range(self._columns)
        check_value(x, valid_rng, f"Значение {y} должно быть в диапазоне: {valid_rng}")

        # Адрес памяти для символа: position * 2
        # надо послать команду записи начинающуюся с адреса в памяти дисплея
        # Разбиваем 16-битное значение на два байта (младший и старший)
        # data = (char_code & 0xFF, (char_code >> 8) & 0xFF)

        # Запись команды - сначала указывается адрес памяти, затем данные
        # VK16K33 требует сначала написать адрес, затем данные (2 байта)
        buf = self._packet
        buf[0] = 2 * x # адрес первого байта знакоместа в памяти дисплея
        bo = 'big' if self._connector.is_big_byteorder() else 'little'
        #print(f"DBF:char_code: 0x{char_code:x}")
        _loc_buf = char_code.to_bytes(2, bo)
        buf[1] = _loc_buf[0]
        buf[2] = _loc_buf[1]
        self._write(buf)

    def set_brightness(self, value: int):
        """Устанавливает яркость всех элементов одновременно."""
        valid_rng = range(0x10)
        check_value(value, valid_rng, f"Значение яркости: {value}, вне диапазона: {valid_rng}!")
        val = VK16K33.cmd_set_brightness | value
        self._write(bytes((val,)))

    def _set_display_setup(self, display_on: bool=True, blink_freq: int=0):
        """Управляет режимом дисплея и морганием VK16K33.
            :param display_on: bool — включить (True) или выключить (False) дисплей
            :param blink_freq: int — частота моргания
                0 - моргание отключено
                1 - моргание 2 Гц
                2 - моргание 1 Гц
                3 - моргание 0.5 Гц"""
        valid_rng_blink = range(4)
        check_value(blink_freq, valid_rng_blink, f"Значение blink_freq: {blink_freq} должно быть в диапазоне: {valid_rng_blink}!")
        # Бит включения дисплея D (0x04)
        on_bit = 0x01 if display_on else 0x00
        cmd = VK16K33.cmd_display_setup | blink_freq << 1 | on_bit
        self._write(bytes((cmd,)))
        #
        self._blink_freq = blink_freq
        self._display_on = display_on

    # IDisplayController
    def set_shutdown(self, value: bool):
        """Если value Истина, то дисплей переводится в режим shutdown/выключено"""
        self._set_standby(value=value)

    def init(self, columns: int = 4, rows: int = 1, value: int = 0):
        """Производит аппаратную инициализацию.
        :param value - Определяет тип инициализации.
        :param columns - Количество столбцов, элементов дисплея;
        :param rows - количество строк, элементов дисплея;"""
        if columns <= 0 or rows <= 0:
            raise ValueError(f"Неверное значение строк: {rows} или столбцов: {columns}!")
        self._columns = columns
        # количество знакомест дисплея в высоту
        self._rows = rows
        #
        self._set_standby(value=False)
        self._set_display_setup(display_on=True, blink_freq=0)

    # IDisplayController
    def get_columns(self) ->int:
        return self._columns

    # IDisplayController
    def get_rows(self) ->int:
        return self._rows

    def blink(self, blink_freq: int):
        """Управляет морганием дисплея.
        :param blink_freq — частота моргания
            0 - моргание отключено
            1 - моргание 2 Гц
            2 - моргание 1 Гц
            3 - моргание 0.5 Гц"""
        self._set_display_setup(True, blink_freq)
    
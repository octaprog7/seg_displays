"""
MicroPython UART TM1652 segment display driver
"""

# micropython
# MIT license

from sensor_pack_2.base_sensor import check_value   # DeviceEx
from lib_displays.display_controller_mod import ICharDisplayController

import time
import micropython
#from collections import namedtuple
from machine import UART


@micropython.viper
def _reverse4bits(n : int) -> int:
    """
    Переворачивает порядок младших 4 бит числа n.

    Параметры:
    n (int): Целое число в диапазоне 0-15, представляющее 4-битное значение.

    Возвращает:
    int: Целое число, у которого порядок 4 бит перевёрнут.

    В микросхеме TM1652 4-битный код яркости передается в формате с инверсией порядка бит (старшие и младшие биты идут в обратном порядке) по сравнению с естественным значением,
    которое удобно задавать человеку.
    """
    res = 0
    for i in range(4):
        if (n >> i) & 1:
            res |= 1 << (3 - i)
    return res


class TM1652(ICharDisplayController):
    CMD_SET_DIGITS = micropython.const(0x08)
    # установка яркости
    CMD_SET_BRIGHTNESS = micropython.const(0x18)
    # команда включения или сброса устройства
    CMD_RESET_AFTER_PWR_ON = micropython.const(0x01)
    BRIGHTNESS_ON_BIT = micropython.const(0x10)
    CMD_OFF_DISPLAY = micropython.const(0xEF)

    def __init__(self, uart: UART, delay_ms: int = 4):
        """
        :param uart: настроенный последовательный порт RS-232
        :param delay_ms: задержка в мс., после операции записи в порт self._uart, необходима для правильной работы TM1652
        """
        self._uart = uart
        self._delay = delay_ms
        # количество знакомест дисплея в ширину
        self._columns = None
        # количество знакомест дисплея в высоту
        self._rows = None
        # хранение значения установленной ранее яркости
        self._brightness = 3
        self._digit_buffer = bytearray(5)  # буфер для чисел времени
        self._bright_buffer = bytearray(2)  # буфер для пересылки яркости
        #
        self._send_cmd(bytearray((TM1652.CMD_RESET_AFTER_PWR_ON,)))

    def _send_cmd(self, buf: bytes):
        self._uart.write(buf)
        time.sleep_ms(self._delay)

    def _fast_write(self, buf: bytes):
        """Записывает(быстро) в порт сырые данные из buf, где buf:bytearray длиной 5(ПЯТЬ) байт.
        В первом байте должен быть код команды TM1652.CMD_SET_DIGITS,
        остальные 4 ячейки должны содержать битовые значения включенных сегментов 4-x знакомест."""
        if 5 != len(buf):
            raise ValueError("Длина buf должна равняться 5-ти байтам!")
        self._send_cmd(buf)

    def set_all(self, char_codes: bytes):
        """для контроллеров, не поддерживающих запись в отдельные позиции."""
        buf = self._digit_buffer
        buf[0] = TM1652.CMD_SET_DIGITS
        buf[1:] = char_codes
        self._fast_write(buf)

    def _set_shutdown_brightness(self, destination: bytearray, shutdown: bool, brightness: int):
        """Общий код для методов: set_shutdown, set_brightness"""
        buf = destination
        buf[0] = TM1652.CMD_SET_BRIGHTNESS  # команда управления дисплеем и яркостью
        if shutdown:
            # ВЫКЛючить дисплей - сбросить бит включения (бит 4 = 0)
            buf[1] = TM1652.CMD_OFF_DISPLAY & brightness
        else:
            # ВКЛючить дисплей с яркостью brightness
            buf[1] = TM1652.BRIGHTNESS_ON_BIT | (_reverse4bits(brightness) & 0x0F)
        #
        self._send_cmd(buf)
        self._brightness = brightness

    def get_brightness(self) -> int:
        """Возвращает значение установленной ранее яркости"""
        return self._brightness

    # IDisplayController
    def set_brightness(self, value: int):
        """
        Установка яркости дисплея.
        :param value: Яркость дисплея от 0 до 7
        :return:
        """
        check_value(value, range(8), f"Яркость вне диапазона: {value}")
        buf = self._bright_buffer
        self._set_shutdown_brightness(buf, False, value)

    def set_shutdown(self, value: bool):
        """
        Если value == True, дисплей в режим shutdown (выключено),
        иначе дисплей включён.
        """
        buf = self._bright_buffer
        self._set_shutdown_brightness(buf, value, self.get_brightness())

    def init(self, columns: int, rows: int, value: int = 0):
        """Первоначальная настройка дисплея. Вызывать сразу после конструктора!"""
        if columns <= 0 or rows <= 0:
            raise ValueError(f"Неверное значение строк: {rows} или столбцов: {columns}!")
        self._columns = columns
        self._rows = columns
        #
        self._send_cmd(bytearray((TM1652.CMD_RESET_AFTER_PWR_ON,)))  # команда включения, документация TM1652
        #
        self.set_shutdown(True)  # ВЫКлючаю дисплей
        self.set_brightness(7 // 2)
        # self.clear()
        self.set_shutdown(False) # ВКлючаю дисплей

    def get_columns(self) -> int:
        """Возвращает кол-во столбцов элементов дисплея."""
        return self._columns

    # IDisplayController
    def get_rows(self) -> int:
        """Возвращает кол-во строк элементов дисплея."""
        return self._rows
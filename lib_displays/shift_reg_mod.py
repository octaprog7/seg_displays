"""
 Модуль для дисплея на основе 8-битного регистр сдвига с последовательным входом и параллельным выходом (например 74HC595)
"""

# micropython
# MIT license

from machine import Pin
#from micropython import const
from sensor_pack_2 import bus_service
# from sensor_pack_2.base_sensor import DeviceEx #, check_value
from lib_displays.display_controller_mod import ICharDisplayController

# Пример инициализация SPI (укажите свои пины!)
# Замечание по значению параметра baudrate.
# В datasheet на 74HC595 (Nexperia 74HC595; 74HCT595; Rev. 12 — 20 March 2024) указана тактовая частота 91 МГц (VCC=4.5 В) на входе SHCP (shift register clock input)
# Это значение недоступно в практике DIY. Я не советую превышать значение 10 МГц, если вы хотите устойчивой работы!
# bus = SPI(1, baudrate=1_000_000, polarity=0, phase=0, firstbit=SPI.MSB, bits=8, sck=6, mosi=7, miso=2)    ESPC3-Zero
# latch = Pin(8, mode=Pin.OUT, pull=Pin.PULL_UP, value=1)  # Пин Latch (фиксатор данных)

class SPLReg8(ICharDisplayController):
    """Программное представление дисплея на основе регистра сдвига с параллельной загрузкой 74HC595"""

    def __init__(self, adapter: bus_service.SpiAdapter, load_out: Pin):
        """
        :param adapter:  адаптер шины (должен быть предварительно настроен, SpiAdapter(bus, data_mode = None))
        :param load_out: вывод МК, управляющий выводом загрузки данных сдвигового регистра в выходной буфер чипа/микросхемы
        """
        self._adapter = adapter
        #:param inverted_out: если Истина, то сегмент включается нулем (индикатор(ы) с общим АНОДОМ, иначе сегмент включается единицей (общий КАТОД))
        #self._inverted_out = inverted_out
        self._load_out = load_out
        # количество знакомест дисплея в ширину
        self._columns = None
        # количество знакомест дисплея в высоту
        self._rows = None

#    def (self) -> bool:
#        """Возвращает Истина, если в конструкторе параметр inverted_out был Истина"""
#        return self._inverted_out

    def _write(self, buf: bytes):
        """Запись сырых данных по шине адресату.
        :param buf - массив данных для передачи по шине.
        """
        return self._adapter.write(self._load_out, buf)

    # IDisplayController
    def get_columns(self) ->int:
        """Возвращает кол-во столбцов элементов дисплея."""
        return self._columns

    # IDisplayController
    def get_rows(self) ->int:
        """Возвращает кол-во строк элементов дисплея."""
        return self._rows

    def set_all(self, char_codes: bytes):
        """для контроллеров, не поддерживающих запись в отдельные позиции."""
        self._write(char_codes)

    # IDisplayController
    def init(self, columns: int = 4, rows: int = 1, value: int = 0):
        """Первоначальная настройка дисплея. Вызывать сразу после конструктора!"""
        if columns <= 0 or rows <= 0:
            raise ValueError(f"Неверное значение строк: {rows} или столбцов: {columns}!")
        self._columns = columns
        self._rows = columns

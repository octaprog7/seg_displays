"""Работа с дисплеем на основе MAX7219. 8 знакомест. SPI."""
from machine import Pin, SPI
from collections import namedtuple
from seg_displ_utils import get_board_info
import sys, os
import time
import gc

from sensor_pack_2.bus_service import SpiAdapter
from lib_displays.max7219display import MAX7219Display
from lib_displays.max7219mod import MAX7219

wait_func = time.sleep_ms

if __name__ == "__main__":
    # Осторожно с baudrate! Если у вас символы 'прыгают' по дисплею, тогда снижайте этот параметр.
    bi = get_board_info()
    print(bi)
    if "ESP32C3 module with ESP32C3" in bi.machine:
        bus = SPI(1, baudrate=5_000_000, polarity=0, phase=0, firstbit=SPI.MSB, sck=Pin(4), mosi=Pin(6), miso=Pin(5))
    if "Raspberry Pi Pico" in bi.machine:
        bus = SPI(0, baudrate=5_000_000, polarity=0, phase=0, bits=8, firstbit=SPI.MSB, sck=Pin(18), mosi=Pin(19), miso=Pin(16))

    if bus is None:
        raise ValueError("Шина не настроена!")

    #print(bus)
    adapter = SpiAdapter(bus=bus, data_mode=None)
    # сигнал для шины SPI (slave_select)
    slave_select = Pin(7, mode=Pin.OUT, pull=Pin.PULL_UP, value=1)
    display_controller = MAX7219(adapter=adapter, chip_select=slave_select)
    display_controller.init(columns=8, rows=1)
    #
    display_controller.set_brightness(9)
    display = MAX7219Display(display_controller)
    # Pi demo
    display.show_by_pos("3.1415926")
    wait_func(3_000)
    # Time demo
    spacer = '-'
    cnt = 0
    for _ in range(15_000):
        lc = time.localtime()
        slc = f"{lc[3]:02}{spacer}{lc[4]:02}{spacer}{lc[5]:02}"
        display.show_by_pos(slc, 0, 0)
        wait_func(1000)
        cnt += 1
        # если у вас программа ведет себя непредсказуемо, удалите комментарии с последующих 4-ч строк для 'уборки мусора'!
        if 0 == cnt % 5:
            gc.collect()
            cnt = 0
            print("collect")
        #obj_count = gc.collect()	# без вызова collect() у меня код продолжал работать, а дисплей ничего не отображал! Выброса исключений не было!
        # print(f"obj_count: {obj_count}")

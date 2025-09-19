"""Работа с дисплеем на основе 74HC595. 4 знакоместа. SPI."""
from machine import Pin, SPI
from lib_displays.shift_reg_mod import SPLReg8
from lib_displays.shift_reg_display import ShiftReg8Display
from sensor_pack_2.bus_service import SpiAdapter
import random
import time

wait_func = time.sleep_ms

def get_rnd_4digit() -> int:
    return random.randint(1000, 9999)


def run():
    # Инициализация SPI (укажите свои пины и контроллер)
    #spi = SPI(1, baudrate=1_000_000, polarity=0, phase=0, firstbit=SPI.MSB, bits=8, sck=6, mosi=7, miso=2)
    latch = Pin(8, mode=Pin.OUT, pull=Pin.PULL_UP, value=1)  # Пин Latch (фиксатор данных)


    bus = SPI(1, baudrate=1_000_000, polarity=0, phase=0, firstbit=SPI.MSB, bits=8, sck=6, mosi=7, miso=2)
    adapter = SpiAdapter(bus=bus, data_mode=None)
    controller = SPLReg8(adapter=adapter, load_out=latch)
    controller.init(columns=4, rows=1)
    display = ShiftReg8Display(controller)
    display.init()

    display.show_by_pos("3.1415", 3)
    wait_func(3_000)
    display.clear()
    wait_func(3_000)
    # display.show_by_pos("123", 2)
    #wait_func(3_000)
    #
    for _ in range(10_000):
        digits = get_rnd_4digit()
        print(digits)
        display.show_by_pos(str(digits))
        time.sleep_ms(3_000)


if __name__ == "__main__":
    run()
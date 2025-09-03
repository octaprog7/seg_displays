"""Работа с дисплеем на основе VK16K33. 4 знакоместа. I2C."""

from machine import Pin, I2C
from seg_displ_utils import get_board_info
import time

from lib_displays.vk16k33display import VK16K33Display
#import gc

from sensor_pack_2.bus_service import I2cAdapter
from lib_displays.vk16k33mod import VK16K33

wait_func = time.sleep_ms

def get_chunk(source: str, start: int, length: int) -> str:
    while True:
        if start  < len(source):
            yield source[start: start + length]
        else:
            break
        start += length


if __name__ == "__main__":
    bi = get_board_info()
    print(bi)
    # настройка шины I2C верна только для плат RP2040 Pico, RP2040 Pico W
    bus = I2C(id=1, scl=Pin(7), sda=Pin(6), freq=400_000)   # Pico, Pico W
    # для других плат используйте другие настройки!
    # bus = I2C(id=X, scl=Pin(Y), sda=Pin(Z), freq=400_000)
    adapter = I2cAdapter(bus=bus)
    wait_func(1)
    display_controller = VK16K33(adapter=adapter, address=0x70)
    display_controller.init(columns=4, rows=1)
    display_controller.set_brightness(10)
    display = VK16K33Display(display_controller)
    display.init()
    #
    demo_source_14seg = "0123456789AaBbCcDdEeFfGgHhIiJjKkLlMmNnOoPpQqRrSsTtUuVvWwXxYyZz"
    np = display.get_non_printable()
    print(f"non printable: {np}")
    #
    chunk_length = display.get_columns()
    start = 0
    cnt = 0
    for chunk in get_chunk(demo_source_14seg, start, chunk_length):
        display.show_by_pos(chunk, 0)
        if 5 == cnt:    # 2 - моргание дисплея с частотой 2 Гц
            display_controller.blink(1)
        cnt+=1
        wait_func(3000)

    display.clear()
"""Работа с дисплеем We Act Digital Tube 8.8.8.8. 4 знакоместа. UART."""
import micropython
from collections import namedtuple
from lib_displays.TM1652mod import TM1652
from lib_displays.tm1652display import WADigitalTube
from machine import UART, Pin
import time

# Часы, минуты, секунды; Год, месяц, день
level_3_numbers = namedtuple('level_3_numbers', "lvl_0 lvl_1 lvl_2")
# время (ЧЧ:MM) для отображения на ч-х сегментах дисплея
# middle_flag - флаг 'бега' секунд в середине дисплеев, предназначенных для отображения времени
four_seg_t = namedtuple("four_seg_t", "seg_0 seg_1 seg_2 seg_3 middle_flag")

@micropython.native
def get_display_digits(source: level_3_numbers, lvl_0_offset: int = 0) -> four_seg_t:
    """Преобразует поля source в four_seg_t для сегментов дисплея."""
    l_0 = source.lvl_0 + lvl_0_offset
    return four_seg_t(seg_0=l_0 // 10, seg_1=l_0 % 10, seg_2=source.lvl_1 // 10,
                      seg_3=source.lvl_1 % 10, middle_flag= 0 == source.lvl_2 % 2)

def four_seg_to_str(source: four_seg_t, leading_zero: bool = True) -> str:
    """Преобразует четыре числовых значения в строку.
    :param source - значения отдельных сегментов;
    :param leading_zero - если Истина, то первый ноль отображается;
    """
    dp = "." if source.middle_flag else ""
    _seg_0 = ' ' if 0 == source.seg_0 and not leading_zero else source.seg_0
    return f"{_seg_0}{source.seg_1}{dp}{source.seg_2}{source.seg_3}"

if __name__ == "__main__":
    # не забывайте про параметр конструктора tx!!!
    # вывод платы tx вы должны подключить к ВХоду дисплея RX!!!
    # и питание +5 V, GND! Преобразователь уровня не нужен!
    uart = UART(0, baudrate=19200, bits=8, parity=1, stop=1, tx=Pin(16))
    controller = TM1652(uart=uart, delay_ms=7)
    controller.init(columns=4, rows=1)
    tube = WADigitalTube(controller)
    tube.init()
    tube.show_by_pos('Erro')
    time.sleep_ms(3_000)
    tube.clear()
    time.sleep_ms(2_000)
    # отображение местного времени на дисплее
    for _ in range(100):
        t = time.localtime()
        l3 = level_3_numbers(t[3], t[4], t[5])
        dd = get_display_digits(l3, 0)
        fs = four_seg_to_str(dd, False)
        tube.show_by_pos(fs)
        time.sleep_ms(1000)




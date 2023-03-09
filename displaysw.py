# simple test display
import rp2
from rp2 import PIO
import tm1637
from machine import I2C, Pin
from gpio_lcd import *
from pico_i2c_lcd import I2cLcd

"""
The Display Base class - might not actually be needed
But here to ensure we do not have a duckTyping problem
"""
class Display:

    def reset(self):
        print(f"reset NOT IMPLEMENTED in {type(self).__name__}")

    def showNumber(self, number):
        print(f"showNumber NOT IMPLEMENTED! in {type(self).__name__}")

    def showText(self, text):
        print(f"showText NOT IMPLEMENTED! in {type(self).__name__}")

    def scroll(self, text, speed=250):
        print(f"Scroll NOT IMPLEMENTED! in {type(self).__name__}")


class SevenSegmentDisplay(Display):
    def __init__(self, clk=20, dio=21):
        self._tm = tm1637.TM1637(clk=Pin(clk), dio=Pin(dio))

    """ 
    clear the display screen
    """
    def reset(self):
        self._tm.write([0, 0, 0, 0])

    """
    show a single number
    """
    def showNumber(self, number):
        self._tm.number(number)

    """
    Show two numbers optionally separated by a colon
    by default, the colon is shown
    """
    def showNumbers(self, num1, num2, colon=True):
        self._tm.numbers(num1, num2, colon)

    """
    Show a string - only first 4 characters will be shown
    for anything bigger than 4 characters.
    """
    def showText(self, text):
        self._tm.show(text)

    """
    Scroll a longer text - note that this will use a sleep
    call to pause between movements.
    """
    def scroll(self, text, speed=250):
        self._tm.scroll(text, speed)

class SevenSegmentDisplayRaw(Display):
    def __init__(self, pinstart=2, digstart=10):
        self._digits = [
            0b11000000, # 0
            0b11111001, # 1
            0b10100100, # 2 
            0b10110000, # 3
            0b10011001, # 4
            0b10010010, # 5
            0b10000010, # 6
            0b11111000, # 7
            0b10000000, # 8
            0b10011000, # 9
            ]
        self._sm = rp2.StateMachine(0, sevseg, freq=2000, out_base=Pin(pinstart), sideset_base=Pin(digstart))
        self._sm.active(1)
  
    def segmentize(self, num):
        return (
            self._digits[num % 10] | self._digits[num // 10 % 10] << 8
            | self._digits[num // 100 % 10] << 16 
            | self._digits[num // 1000 % 10] << 24 
        )

    def showNumber(self, n):
        self._sm.put(self.segmentize(n))

class LCDDisplay(Display):
    def __init__(self, rs=5, e=4, d4=3, d5=2, d6=1, d7=0):
        print("LCDDisplay Constructor")
        self._lcd = GpioLcd(rs_pin=Pin(rs),
              enable_pin=Pin(e),
              d4_pin=Pin(d4),
              d5_pin=Pin(d5),
              d6_pin=Pin(d6),
              d7_pin=Pin(d7),
              num_lines=2, num_columns=16)

    def __init__(self, sda=0, scl=1):
        print("LCDDisplay (I2C) Constructor")
        i2c = I2C(0, sda=Pin(0), scl=Pin(1), freq=400000)
        I2C_ADDR = i2c.scan()[0]
        self._lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)

    """ 
    clear the display screen
    """
    def reset(self):
        print("LCDDisplay: reset")
        self._lcd.clear()

    """
    show a single number
    """
    def showNumber(self, number, row=0, col=0):
        print(f"LCDDisplay - showing number {number} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(f"{number}")

    """
    Show two numbers optionally separated by a colon
    by default, the colon is shown
    """
    def showNumbers(self, num1, num2, colon=True, row=0, col=0):
        print(f"LCDDisplay - showing numbers {num1}, {num2} at {row},{col}")
        self._lcd.move_to(col, row)
        colsym = ":" if colon else " "
        self._lcd.putstr(f"{num1}{colsym}{num2}")

    """
    Show a string - only first 4 characters will be shown
    for anything bigger than 4 characters.
    """
    def showText(self, text, row=0, col=0):
        print(f"LCDDisplay - showing text {text} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(text)

    """
    Scroll a longer text - note that this will use a sleep
    call to pause between movements.
    """
    def scroll(self, text, speed=250):
        print("LCDDisplay: Scroll - Not yet implemented")

"""

"""
class DotMatrixDisplay(Display):


@rp2.asm_pio(out_init=[PIO.OUT_LOW]*8, sideset_init=[PIO.OUT_LOW]*4)
def sevseg():
    wrap_target()
    label("0")
    pull(noblock)           .side(0)      # 0
    mov(x, osr)             .side(0)      # 1
    out(pins, 8)            .side(1)      # 2
    out(pins, 8)            .side(2)      # 3
    out(pins, 8)            .side(4)      # 4
    out(pins, 8)            .side(8)      # 5
    jmp("0")                .side(0)      # 6
    wrap()


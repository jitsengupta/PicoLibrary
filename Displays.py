"""
# Displays.py
# A collection of various text-based displays
# Currently supports 4-digit seven-segment displays - both with a tm1637 backpack
# and without (using PIO)
# And also LCD 1602 displays - both using an i2c backpack as well as GPIO
# Only supports number and basic text displays - PIO 7 seg only supports number
# Author: Arijit Sengupta
"""

from machine import Pin, I2C, SPI
import rp2
import time
from rp2 import PIO
import tm1637
from gpio_lcd import *
from pico_i2c_lcd import I2cLcd
from ssd1306 import SSD1306_I2C
import lcd128_32_fonts
from lcd128_32 import lcd128_32
import max7219

class Display:
    """
    The Display Base class - might not actually be needed
    But here to ensure we do not have a duckTyping problem
    """

    def reset(self):
        print(f"reset NOT IMPLEMENTED in {type(self).__name__}")

    def showNumber(self, number):
        print(f"showNumber NOT IMPLEMENTED! in {type(self).__name__}")

    def showText(self, text):
        print(f"showText NOT IMPLEMENTED! in {type(self).__name__}")

    def scroll(self, text, speed=250):
        print(f"Scroll NOT IMPLEMENTED! in {type(self).__name__}")


class SevenSegmentDisplay(Display):
    """
    Seven Segment Display class - implements a 4-digit seven segment display
    Decimal points not supported - colon can be used when showing two numbers
    """

    def __init__(self, clk=16, dio=17):
        self._tm = tm1637.TM1637(clk=Pin(clk), dio=Pin(dio))

    def reset(self):
        """ clear the display screen  """
        
        self._tm.write([0, 0, 0, 0])

    def showNumber(self, number):
        """ show a single number """
        
        self._tm.number(number)

    def showNumbers(self, num1, num2, colon=True):
        """  Show two numbers optionally separated by a colon by default, the colon is shown """
        
        self._tm.numbers(num1, num2, colon)

    def showText(self, text):
        """
        Show a string - only first 4 characters will be shown
        for anything bigger than 4 characters.
        """
        
        self._tm.show(text)

    def scroll(self, text, speed=250):
        """
        Scroll a longer text - note that this will use a sleep
        call to pause between movements.
        """
        
        self._tm.scroll(text, speed)

class SevenSegmentDisplayRaw(Display):
    """
    A Raw 7 segment display that uses RPi PIO along with internal StateMachine
    to poll 4 digits into the display. All digits are shown always so there will be
    leading zeros for numbers under 4 digits
    """
    
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
  
    def _segmentize(self, num):
        return (
            self._digits[num % 10] | self._digits[num // 10 % 10] << 8
            | self._digits[num // 100 % 10] << 16 
            | self._digits[num // 1000 % 10] << 24 
        )

    def showNumber(self, n):
        self._sm.put(self._segmentize(n))
        
    def reset(self):
        self._sm.put(0xFFFFFFFF)

class LCDDisplay(Display):
    """
    LCD Display class - currently supports displays with an I2C backpack
    as well as displays directly driven via the d4-d7 pins
    
    Parameters
    --------
    This is important since Python does not have method overloading, we have one init
    to do both parallel as well as i2c displays
    pass rs, e, d4, d5, d6, d7 pin numbers for parallel displays
    
    pass sda, scl, i2cid for i2c displays - default is to use parallel so must pass sda/scl/i2cid
    if using i2c
    
    To connect the display to I2C 0 on GPIO pins 0,1
    usage: LCDDisplay(sda=0, scl=1, i2cid=0)
    
    To connect the display to I2C ID 1 on GPIO pins 2,3
    usage: LCDDisplay(sda=2, scl=3, i2cid=1)
    
    To connect via parallel with rs on pin 5, e on pin 4
    and d4,d5,d6,d7 to pins 3,2,1 and 0:
    usage:  LCDDisplay()  # yeah those are the default so you don't need to send
    usage: LCDDisplay(rs=5, e=4, d4=3, d5=2, d6=1, d7=0) # preferred - you can see how its hooked up
    
    """
    
    def __init__(self, rs=5, e=4, d4=3, d5=2, d6=1, d7=0, *, sda=-1, scl=-1, i2cid=0):
        """
        Combined constructor for the direct-driven displays
        explicitly pass in the sda and scl if you need to use I2C
        """
        
        if sda < 0:
            print("LCDDisplay Constructor")
            self._lcd = GpioLcd(rs_pin=Pin(rs),
                enable_pin=Pin(e),
                d4_pin=Pin(d4),
                d5_pin=Pin(d5),
                d6_pin=Pin(d6),
                d7_pin=Pin(d7),
                num_lines=2, num_columns=16)
        else:
            print("LCDDisplay (I2C) Constructor")
            i2c = I2C(i2cid, sda=Pin(sda), scl=Pin(scl), freq=400000)
            try:
                I2C_ADDR = i2c.scan()[0]
                self._lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
            except:
                raise ValueError('Could not connect to display - check wiring.')

    def reset(self):
        """ 
        clear the display screen
        """
        
        print("LCDDisplay: reset")
        self._lcd.clear()

    def showNumber(self, number, row=0, col=0):
        """
        show a single number
        """
        
        print(f"LCDDisplay - showing number {number} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(f"{number}")

    def showNumbers(self, num1, num2, colon=True, row=0, col=0):
        """
        Show two numbers optionally separated by a colon
        by default, the colon is shown
        """
        
        print(f"LCDDisplay - showing numbers {num1}, {num2} at {row},{col}")
        self._lcd.move_to(col, row)
        colsym = ":" if colon else " "
        self._lcd.putstr(f"{num1}{colsym}{num2}")

    def showText(self, text, row=0, col=0):
        """
        Show a string - only first 4 characters will be shown
        for anything bigger than 4 characters.
        """
        
        print(f"LCDDisplay - showing text {text} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(text)

    def scroll(self, text, row=0, speed=100, skip=2):
        """
        A very simple scroll implementation
        Scrolls some text right to left in a row

        speed is essentially the delay between refresh - lower the better
        skip is the number of chars to skip for the next refresh
        higher number will be faster but may be jerky. lower will be smooth
        but slower.

        I2C devices may not have best scrolling performance. Works
        better with GPIO-driven displays
        """

        print(f"LCDDisplay - scrolling text {text} in row {row}")
        for p in range(0,len(text)+skip, skip):
            curst = (text+' '*(16+skip))[p:p+16]
            for c in range(16,0,-1):
                self._lcd.move_to(c-1, row)
                self._lcd.putchar(curst[c-1])
            time.sleep(speed/1000)

class DotMatrixDisplay(Display):
    """
    An implementation of the MAX7219 Dot Matrix display
    Fairly simplistic implementation - tested only with simulator so far 
    """

    def __init__(self, sck=18, mosi=19, cs=17):
        self._spi = SPI(0, baudrate=10000000, polarity=1, phase=0, sck=Pin(sck), mosi=Pin(mosi))
        # Create matrix display instant, which has four MAX7219 devices.
        self._dot = max7219.Matrix8x8(self._spi, Pin(cs, Pin.OUT), 4)
        self._dot.brightness(10)
        self.reset()

    def reset(self):
        #Clear the display.
        self._dot.fill(0)
        self._dot.show()

    def showNumber(self, number, row = 0, col = 0):
        self._dot.text(str(number), row, col, 1)
        self._dot.show()

    def showText(self, text, row = 0, col = 0):
        self._dot.text(text, row, col, 1)
        self._dot.show()

    def scroll(self, text, speed=50):
        #Get the message length
        length = len(text)
        column = (length * 8)
        for x in range(32, -column, -1):     
            #Clear the display
            self._dot.fill(0)
            # Write the scrolling text in to frame buffer
            self._dot.text(text,x,0,1)
            #Show the display
            self._dot.show()
      
            #Set the Scrolling speed. Here it is 50mS.
            time.sleep(speed/1000)

class LCDHiResDisplay(Display):
    """
    LCDHiResDisplay - implements an LCD display which gives access to individual pixels
    
    Only supports I2C connection for now. Pass in sda, scl, i2cid, width and height
    
    Usage:
    Connect to I2C0 on sda to pin 0 and scl to pin 1:
    
    LCDHiResDisplay(sda=0, scl=1, i2cid=0, width=128, height=32)
    
    Connect to I2C0 on sda to pin 20, scl to pin 21:
    LCDHiResDisplay(sda=20, scl=21, i2cid=0, width=128, height=32) # default values
    
    Note that graphics outputs are not supported yet in this library.    
    """
    
    def __init__(self, sda=20, scl=21, i2cid=0, width=128, height=32):
        print("LCDHiResDisplay (I2C) Constructor")
        i2c = I2C(i2cid, sda=Pin(sda), scl=Pin(scl), freq=400000)
        I2C_ADDR = i2c.scan()[0]
        try:
            I2C_ADDR = i2c.scan()[0]
            self._lcd = lcd128_32(sda, scl, i2cid, I2C_ADDR)
            self.reset()
        except:
            raise ValueError('Could not connect to display - check wiring.')

    def reset(self):
        self._lcd.Clear()
        
    def showNumber(self, number, row=0, col=0):
        self._lcd.Cursor(row,col)
        self._lcd.Display(str(number))

    def showText(self, text, row=0, col=0):
        self._lcd.Cursor(row,col)
        self._lcd.Display(text)

    
class OLEDDisplay(Display):
    """
    OLEDDisplay class - implements an OLED display
    
    Only supports I2C connection for now. Pass in sda, scl, i2cid, width and height
    
    Usage:
    Connect to I2C0 on sda to pin 0 and scl to pin 1:
    
    OLEDDisplay(sda=0, scl=1, i2cid=0, width=128, height=64)
    
    Connect to I2C1 on sda to pin 26, scl to pin 27:
    OLEDDisplay(sda=26, scl=27, i2cid=1, width=128, height=64) # default values
    
    Note that graphics outputs are not supported yet in this library.
    """

    def __init__(self, sda=26, scl=27, i2cid=1, width=128, height=64):
        self._i2c = I2C(i2cid, sda=Pin(sda), scl=Pin(scl), freq=400000)
        self._oled = SSD1306_I2C(width, height, self._i2c)
        self.reset()

    def reset(self):
        self._oled.fill(0)
        self._oled.show()
        
    def showNumber(self, number, row=0, col=0):
        self._oled.text(str(number), row, col, 1)
        self._oled.show()

    def showText(self, text, row=0, col=0):
        self._oled.text(text, row, col, 1)
        self._oled.show()

class MorseDisplay(Display):
    """
    This is a fun class - implement a Morse code display
    This can play the Morse code via a Buzzer, or show
    the code via a light, or even display it in another
    display.
    
    We need to make sure the other display is not another
    MorseDisplay though
    """
        
    def __init__(self, buz=None, light=None, otherDisplay=None):
        self._buz = buz
        self._light = light
        if isinstance(otherDisplay, OLEDDisplay) or isinstance(otherDisplay, LCDDisplay):
            self._dp = otherDisplay
        else:
            self._dp = None
            print(f"Sorry, {type(otherDisplay).__name__} isn't supported")
        self._morsedict = {'A': '.-', 'B': '-...', 'C': '-.-.', 'D': '-..', 'E': '.', 'F': '..-.', 'G': '--.', 'H': '....',
            'I': '..', 'J': '.---', 'K': '-.-', 'L': '.-..', 'M': '--', 'N': '-.', 'O': '---', 'P': '.--.',
            'Q': '--.-', 'R': '.-.', 'S': '...', 'T': '-', 'U': '..-', 'V': '...-', 'W': '.--', 'X': '-..-',
            'Y': '-.--', 'Z': '--..', '0': '-----', '1': '.----', '2': '..---', '3': '...--', '4': '....-',
            '5': '.....', '6': '-....', '7': '--...', '8': '---..', '9': '----.'}

    def showNumber(self, number):
        """ Just convert the number to a string and show it """
        
        showText(self, str(number))

    def showText(self, text):
        """ Displaying a Morse decoded text on the buzzer, light and possibly display """
        
        morse = self._decodeText(text)
        if self._dp is not None:
            self._dp.showText(morse)
        # go through the string each character at a time
        for char in morse:
            # if the character is in our dictionary, then get the code
            if char == ".":
                self._displaydida(100)
            elif char == "-":
                self._displaydida(250)
            else:
                time.sleep_ms(250)
                    
    ####### Local private methods in MorseDisplay - should not be used from outside ####            
    def _decodeText(self, text):
        morse = []
        for char in text.upper():
            if char in self._morsedict:
                morse.append(self._morsedict[char])
            elif char.isspace():
                morse.append(' ')
        return " ".join(morse)
    
    def _displaydida(self, sleeptime):
        if self._buz is not None:
            self._buz.play()
        if self._light is not None:
            self._light.on()
        time.sleep_ms(sleeptime)
        if self._buz is not None:
            self._buz.stop()
        if self._light is not None:
            self._light.off()
        time.sleep_ms(100)

# Internals used by the PIO state machine
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

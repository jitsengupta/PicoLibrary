"""
# Displays.py
# A collection of various text-based displays
# Note - as of 7/31/24 only the LCDDisplay is implemented in this module
# Use OtherDisplays.py, GraphicDisplays.py and GraphicLCD.py for the rest
# Supports LCD 1602 displays - both using an i2c backpack as well as GPIO
# Only supports number and basic text displays 
# Author: Arijit Sengupta
"""

from machine import Pin, I2C, SPI
import time
from Log import *
from gpio_lcd import *
from pico_i2c_lcd import I2cLcd

class Display:
    """
    The Display Base class - might not actually be needed
    But here to ensure we do not have a duckTyping problem
    """

    def reset(self):
        Log.e(f"reset NOT IMPLEMENTED in {type(self).__name__}")
        
    def clear(self):
        self.reset()

    def showNumber(self, number):
        Log.e(f"showNumber NOT IMPLEMENTED! in {type(self).__name__}")

    def showText(self, text):
        Log.e(f"showText NOT IMPLEMENTED! in {type(self).__name__}")

    def scroll(self, text, speed=250):
        Log.e(f"Scroll NOT IMPLEMENTED! in {type(self).__name__}")

class LCDDisplay(Display):
    """
    LCD Display class - currently supports displays with an I2C backpack
    as well as displays directly driven via the d4-d7 pins
    
    Parameters
    --------
    This is important since Python does not have method overloading, we have one init
    to do both parallel as well as i2c displays
    pass rs, e, d4, d5, d6, d7 pin numbers for parallel displays
    
    pass sda and scl for i2c displays - default is to use parallel so must pass
    both sda/scl if using i2c
    
    To connect the display to I2C 0 on GPIO pins 0,1
    usage: LCDDisplay(sda=0, scl=1)
    
    To connect the display to I2C ID 1 on GPIO pins 2,3
    usage: LCDDisplay(sda=2, scl=3)
    
    To connect via parallel with rs on pin 5, e on pin 4
    and d4,d5,d6,d7 to pins 3,2,1 and 0:
    usage:  LCDDisplay()  # yeah those are the default so you don't need to send
    usage: LCDDisplay(rs=5, e=4, d4=3, d5=2, d6=1, d7=0) # preferred - you can see how its hooked up
    
    """
    
    def __init__(self, rs=5, e=4, d4=3, d5=2, d6=1, d7=0, *, sda=-1, scl=-1):
        """
        Combined constructor for the direct-driven displays
        explicitly pass in the sda and scl if you need to use I2C
        """
        
        if sda < 0:
            Log.i("LCDDisplay Constructor")
            self._lcd = GpioLcd(rs_pin=Pin(rs),
                enable_pin=Pin(e),
                d4_pin=Pin(d4),
                d5_pin=Pin(d5),
                d6_pin=Pin(d6),
                d7_pin=Pin(d7),
                num_lines=2, num_columns=16)
        else:
            Log.i("LCDDisplay (I2C) Constructor")
            """
            Lets determine the i2c id from the sda and scl pins
            """
            i2cid = -1 # lets set an invalid value to start with
            if (sda == 0 and scl == 1) or (sda == 4 and scl == 5) or (sda == 8 and scl == 9) or (sda == 12 and scl == 13) or (sda == 16 and scl == 17) or (sda == 20 and scl == 21):    
                i2cid = 0
            elif (sda == 2 and scl == 3) or (sda == 6 and scl == 7) or (sda == 10 and scl == 11) or (sda == 14 and scl == 15) or (sda == 18 and scl == 19) or (sda == 26 and scl == 27):
                i2cid = 1
            else:
                raise ValueError('Invalid SDA/SCL pins')
            i2c = I2C(i2cid, sda=Pin(sda), scl=Pin(scl), freq=400000)
            try:
                I2C_ADDR = i2c.scan()[0]
                self._lcd = I2cLcd(i2c, I2C_ADDR, 2, 16)
            except:
                raise ValueError('Could not connect to display - check wiring.')
        self._working = False

    def reset(self):
        """ 
        clear the display screen
        """
        
        Log.i("LCDDisplay: reset")
        self._lcd.clear()
        self._working = False

    def clear(self, line=-1):
        """
        Clear only a single line - negative to reset
        """

        if line < 0 or line > 1:
            self.reset()
        else:
            self.showText(f'{" "*16}',line)

    def showNumber(self, number, row=0, col=0):
        """
        show a single number
        """
        
        if self._working:
            Log.e("LCDDisplay - Display busy")
            return
        self._working = True
        Log.i(f"LCDDisplay - showing number {number} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(f"{number}")
        self._working = False

    def showNumbers(self, num1, num2, colon=True, row=0, col=0):
        """
        Show two numbers optionally separated by a colon
        by default, the colon is shown
        """
        
        if self._working:
            Log.e("LCDDisplay - Display busy")
            return
        self._working = True
        Log.i(f"LCDDisplay - showing numbers {num1}, {num2} at {row},{col}")
        self._lcd.move_to(col, row)
        colsym = ":" if colon else " "
        self._lcd.putstr(f"{num1}{colsym}{num2}")
        self._working = False

    def showText(self, text, row=0, col=0):
        """
        Show a string - only first 4 characters will be shown
        for anything bigger than 4 characters.
        """
        
        if self._working:
            Log.e("LCDDisplay - Display busy")
            return
        self._working = True
        Log.i(f"LCDDisplay - showing text {text} at {row},{col}")
        self._lcd.move_to(col, row)
        self._lcd.putstr(text)
        self._working = False

    def addShape(self, position, shapearray):
        """
        Add a custom character at a position.
        position must be between 0 and 7
        shapearray needs to be a bytearray that can
        be created by going to
        https://maxpromer.github.io/LCD-Character-Creator/
        and then copying the bytes into a bytearray as a list of hex values
        as in the example below:

        d.addShape(1, [0x00,0x0A,0x0A,0x00,0x11,0x0E,0x04,0x00]) # a smiley face
        d.showText(chr(1), 0,5) # show the smiley face at position 5 of row 0
        """
        
        if position < 0 or position > 7:
            raise ValueError('Position must be between 0 and 7.')
        if len(shapearray) != 8:
            raise ValueError('Make sure array is exactly 8 bytes')
        self._lcd.custom_char(position, shapearray)

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

        if self._working:
            Log.e("LCDDisplay - Display busy")
            return
        self._working = True
        Log.i(f"LCDDisplay - scrolling text {text} in row {row}")
        for p in range(0,len(text)+skip, skip):
            curst = (text+' '*(16+skip))[p:p+16]
            for c in range(16,0,-1):
                self._lcd.move_to(c-1, row)
                self._lcd.putchar(curst[c-1])
            time.sleep(speed/1000)
        self._working = False

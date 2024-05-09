"""
# GraphicDisplays.py
# Previously part of Displays.py - split out to improve performance
# of LCD-based displays which are mostly used in our projects
# Currently supports SSD1306-based OLED devices
# and cheap 128x32 I2C LCD devices
# Author: Arijit Sengupta
"""

from Displays import *
from ssd1306 import SSD1306_I2C
import lcd128_32_fonts
from lcd128_32 import lcd128_32

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
        Log.i("LCDHiResDisplay (I2C) Constructor")
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


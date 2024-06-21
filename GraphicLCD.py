"""
# GraphicLCD.py
# Separate from the Display hierarchy
# since it is being created as a subclass of FrameBuffer
# to improve performance. This works well on the Waveshare
# pico display hats but not tested in other devices. The
# commands are based on ST7789 drivers so it may not work
# with other chipsets like the ILI9341. I might eventually
# incorporate the two drivers but for now focusing only
# on the ST7789 since I have one of those.
# Author: Arijit Sengupta
"""
from machine import Pin,SPI,PWM
import framebuf2 as framebuf
import time
import os

REDRGB565   =   0x07E0
GREENRGB565 =   0x001f
BLUERGB565  =   0xf800
WHITERGB565 =   0xffff


class GraphicLCD(framebuf.FrameBuffer):
    """
    GraphicLCD class - based on the Waveshare series of display hats for Pico
    Uses SPI sck @10 MOSI @11 no MISO
    CS @9 DC @8 RST @12 for Display control
    Backlight control @13
    
    Defaults set for the 240x240 display - for different sizes, use the width
    and height parameters. Eg. for the 240x128 use
    
    GraphicLCD(width=240, height=128)
    """
    
    def __init__(self, DC=8, CS=9, SCK=10, MOSI=11, RST=12, BL=13, width=240, height=240, brightness=50):
        self.width = width
        self.height = height
        
        self.cs = Pin(CS,Pin.OUT)
        self.rst = Pin(RST,Pin.OUT)
        self.bl = PWM(Pin(13))
        self.bl.freq(1000)
        self.brightness = brightness
        self.setBrightness(brightness)
        
        self.cs(1)
        self.spi = SPI(1)
        self.spi = SPI(1,1000_000)
        self.spi = SPI(1,100000_000,polarity=0, phase=0,sck=Pin(SCK),mosi=Pin(MOSI),miso=None)
        self.dc = Pin(DC,Pin.OUT)
        self.dc(1)
        self.buffer = bytearray(self.height * self.width * 2)
        super().__init__(self.buffer, self.width, self.height, framebuf.RGB565)
        self.init_display()
        
        self.red   =   REDRGB565
        self.green =   GREENRGB565
        self.blue  =   BLUERGB565
        self.white =   WHITERGB565

    def reset(self):
        """
        Clear the display. By default clear sets the display to a black background.
        """
        self.clear(0)
        
    def clear(self, color=0):
        """
        Clear the display. By default clear sets the display to a black background.
        However, a separate RGB565 color can be sent to clear it with that color.
        """
        self.fill(color)
        self.show()
        
    def setBrightness(self, brightnesslevel = 50):
        """
        Set the backlight brightness to a percent level, default is 50%
        """
        self.brightness = brightnesslevel
        level = int(655.35*brightnesslevel)
        self.bl.duty_u16(level)	#max 65535
        
    def brighter(self, pct=5):
        """
        increase brightness by pct %
        """
        b = self.brightness * (100+pct) / 100
        if b > 100:
            b = 100
        self.setBrightness(b)
        
    def dimmer(self, pct=5):
        """
        Decrease brightness by pct %
        """
        b = self.brighness * (100-pct) /100
        if b < 0:
            b = 0
        self.setBrighness(b)
        

    def color565(self, red, green=0, blue=0):
        """
        Utility function to
        convert red, green and blue values (0-255) into a 16-bit 565 encoding.
        """
        try:
            red, green, blue = red  # see if the first var is a tuple/list
        except TypeError:
            pass
        return (red & 0xf8) << 8 | (green & 0xfc) << 3 | blue >> 3
    
    def showNumber(self, number, row=0, col=0, m=2, c=WHITERGB565, bc=0, show=True):
        """
        Utility method in the same line as the other Display classes
        to show a number at a certain position.
        
        Additional params are size and color
        Size is set to 2 by default since 1 is too small
        bc is background color - default is 0 (black)
        """
        s = str(number)
        self.showText(s, row, col, m, c, bc, show)

    def showText(self, text, row=0, col=0, m=2, c=WHITERGB565, bc=0, show=True):
        """
        Utility method in the same line as the other Display classes
        to show a String at a certain position.
        
        Additional params are size and color
        Size is set to 2 by default since 1 is too small
        bc is background color - default is 0 (black)
        
        The last parameter show is for immediately pushing to framebuf
        if true - if set to False, make all updates and call show for
        improved performance
        """
        # First clear the area needed by drawing a rectangle in bg color
        self.rect(row,col, 8*m*len(text), 8*m, bc, True)
        self.large_text(text, row, col, m, c)
        if show:
            self.show()

    def show(self):
        """
        Push the current framebuffer to SPI. Standard process would be
        to make all updates to the screen using regular Framebuf calls,
        then calling show() once per frame.
        
        Can be set to run on the second core of the Pico if necessary,
        if running on the second core, ensure that no updates are made
        while this method is running.
        
        The last parameter show is for immediately pushing to framebuf
        if true - if set to False, make all updates and call show for
        improved performance
        """
        
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)
    
    # methods below are internal and should not need to be called directly.
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(bytearray([buf]))
        self.cs(1)

    def init_display(self):
        """Initialize dispaly"""  
        self.rst(1)
        self.rst(0)
        self.rst(1)
        
        self.write_cmd(0x36)
        self.write_data(0x70)

        self.write_cmd(0x3A) 
        self.write_data(0x05)

        self.write_cmd(0xB2)
        self.write_data(0x0C)
        self.write_data(0x0C)
        self.write_data(0x00)
        self.write_data(0x33)
        self.write_data(0x33)

        self.write_cmd(0xB7)
        self.write_data(0x35) 

        self.write_cmd(0xBB)
        self.write_data(0x19)

        self.write_cmd(0xC0)
        self.write_data(0x2C)

        self.write_cmd(0xC2)
        self.write_data(0x01)

        self.write_cmd(0xC3)
        self.write_data(0x12)   

        self.write_cmd(0xC4)
        self.write_data(0x20)

        self.write_cmd(0xC6)
        self.write_data(0x0F) 

        self.write_cmd(0xD0)
        self.write_data(0xA4)
        self.write_data(0xA1)

        self.write_cmd(0xE0)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0D)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2B)
        self.write_data(0x3F)
        self.write_data(0x54)
        self.write_data(0x4C)
        self.write_data(0x18)
        self.write_data(0x0D)
        self.write_data(0x0B)
        self.write_data(0x1F)
        self.write_data(0x23)

        self.write_cmd(0xE1)
        self.write_data(0xD0)
        self.write_data(0x04)
        self.write_data(0x0C)
        self.write_data(0x11)
        self.write_data(0x13)
        self.write_data(0x2C)
        self.write_data(0x3F)
        self.write_data(0x44)
        self.write_data(0x51)
        self.write_data(0x2F)
        self.write_data(0x1F)
        self.write_data(0x1F)
        self.write_data(0x20)
        self.write_data(0x23)
        
        self.write_cmd(0x21)

        self.write_cmd(0x11)

        self.write_cmd(0x29)

    def show(self):
        self.write_cmd(0x2A)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xef)
        
        self.write_cmd(0x2B)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0x00)
        self.write_data(0xEF)
        
        self.write_cmd(0x2C)
        
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(self.buffer)
        self.cs(1)

"""
# LightStrip.py
# Re-implementing the old NeoPixel class into a LightStrip class
# Using the built-in neopixel class in MicroPython now
"""

import time, neopixel, machine
from Lights import *
from Log import *

class LightStrip(Light):
    """
    Although technically a composite light, a neopixel is a PIO-driven set of lights
    using a single output pin. So you do not send it composite lights, but just the pin
    it is connected to. It is a composite light because it has multiple lights, but
    they cannot technically be controlled individually.
    """

    FILLS = 0
    CHASES = 1
    RAINBOW = 2

    def __init__(self, name='Neopixel', pin=2, numleds=16, brightness=0.5):
        """
        Constructor for neopixel will create its own internal statemachine
        Note that if any other state machine is running, this will break the existing
        statemachine. This refers to the Pico PIO statemachine, not any software state
        machines.
        """
        
        self._name = name
        self._pin = pin
        self._numleds = numleds
        self._brightness = brightness
        self._running = False
        
        Log.i(f'Creating a neopixel {name} on pin {pin} with {numleds} LEDs')
        self._np = neopixel.NeoPixel(machine.Pin(pin), numleds)

    def on(self):
        """ Turn all LEDs ON - all white """

        self._fill(WHITE)
        self._np.write()
        Log.i(f'{self._name} ON')
    
    def off(self):
        """ Turn all LEDs OFF - all black """
        self._running = False
        time.sleep(0.1)
        self._clear()
        self._np.write()
        Log.i(f'{self._name} OFF')

    def flip(self):
        """ Flip the clors on all the LEDs """
        for x in range(0, self._numleds):
            self._np[x] = (255-self._np[x][0], 255-self._np[x][1], 255-self._np[x][2])
        self.show()
        Log.i(f'{self._name} flipped')

    def setColor(self, color, numPixels= -1):
        """ Turn all LEDs up to a set number of pixels to a specific color """
        if numPixels < 0 or numPixels > self._numleds:
            numPixels = self._numleds
        for i in range(numPixels):
            self._set_pixel(i, color)
        for i in range(numPixels,self._numleds):
            self._set_pixel(i, BLACK)
        self._np.write()
        Log.i(f'{self._name} set color to {color}')

    def setPixel(self, pixelno, color, show=True):
        """
        Turn a single pixel a specific color
        By default the new color is immediately shown.
        To make multiple changes, you can speed up by setting
        show to False, then calling the show method
        """
        self._set_pixel(pixelno, color)
        if show:
            self._np.write()
        Log.i(f'{self._name} set pixel {pixelno} to color {color}')

    def show(self):
        """
        Shows what is in the color buffer. Useful if previous
        setPixel was called without show On
        """
        
        self._np.write()
        
    def setBrightness(self, brightness=0.5):
        """ Change the brightness of the pixel 0-1 range """
        
        self._brightness = brightness
        Log.i(f'{self._name} set brightness to {brightness}')
        
    def run(self, runtype=0):
        """ Run a single cycle of FILLS, CHASES or RAINBOW """
        self._running = True
        if runtype == LightStrip.FILLS:
            Log.i(f'{self._name} running fills')
            for color in COLORS:
                if not self._running:
                    break       
                self.setColor(color)
                time.sleep(0.2)
        elif runtype == LightStrip.CHASES:
            Log.i(f'{self._name} running chases')
            for color in COLORS:
                if not self._running:
                    break       
                self.color_chase(color, 0.01)
        else:
            Log.i(f'{self._name} running rainbow')
            self.rainbow_cycle(0)
        self._running = False


    ################# Internal functions should not be used outside here #################
    def _set_pixel(self, p, color):
        modifiedcolor = tuple(int(col*self._brightness) for col in color)
        self._np[p] = modifiedcolor

    def _clear(self):
        self._np.fill(BLACK)
        pass

    def _fill(self, color):
        self._np.fill(color)
        pass


    def color_chase(self, color, wait):
        for i in range(self._numleds):
            if not self._running:
                break
            self._set_pixel(i, color)
            time.sleep(wait)
            self._np.write()
        time.sleep(0.2)
    
    def wheel(self, pos):
        # Input a value 0 to 255 to get a color value.
        # The colours are a transition r - g - b - back to r.
        if pos < 0 or pos > 255:
            return (0, 0, 0)
        if pos < 85:
            return (255 - pos * 3, pos * 3, 0)
        if pos < 170:
            pos -= 85
            return (0, 255 - pos * 3, pos * 3)
        pos -= 170
        return (pos * 3, 0, 255 - pos * 3)
    
    
    def rainbow_cycle(self, wait):
        for j in range(255):
            if not self._running:
                break
            for i in range(self._numleds):
                rc_index = (i * 256 // self._numleds) + j
                self._set_pixel(i, self.wheel(rc_index & 255))
            self._np.write()
            time.sleep(wait)


# Some color definitions
BLACK = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)
ORANGE = (255, 164, 0)
COLORS = (BLACK, RED, YELLOW, GREEN, CYAN, BLUE, PURPLE, WHITE, ORANGE)


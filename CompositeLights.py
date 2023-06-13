"""
# CompositeLights.py
# A simple inheritance structure showing a fairly abstract CompositeLight
# class that has a set of lights, and two different implementations of it
# Author: Arijit Sengupta
"""

from time import sleep, sleep_ms
import array, time
from machine import Pin
import rp2

class CompositeLight:
    """
    The base CompositeLight class - contains just an array
    and the on, off, run methods that subclasses should potentially override
    The base class simply calls on and off on all internal lights
    that may not be the proper way to turn on the composite
    """
    
    def __init__(self):
        """    # Constructor - just initialize the array of lights """

        print("CompositeLight constructor")
        self._lights = []
        self._running = False
        
    def run(self):
        """
        # Technically this is an abstract method but Python does not
        # correctly support it, so just an empty shell
        """
        
        self._running = True

    def on(self):
        """
        # Turn on all the componets. Note that in does not necessarily
        # get all items in order - but usually does
        """
        
        print("CompositeLight: turning on all lights")
        for l in self._lights:
            l.on()

    def off(self):
        """     # Turn off all the components """

        print("CompositeLight: turning off all lights")
        for l in self._lights:
            l.off()
            
    def singleOn(self, lightno):
        """     # Turn a single light on (and the others off) """

        print(f"CompositieLight - turning only light #{lightno} on")
        for i in range(0,len(self._lights)):
            if i == lightno:
                self._lights[i].on()
            else:
                self._lights[i].off()

    def __str__(self)->str:
        """
        # The __str__ method - add this to any class to generate a 
        # Human readable version of the class
        """
        
        return f"{type(self).__name__} with {len(self._lights)} lights"

        
class TrafficLight(CompositeLight):
    """
    The first subclass of the CompositeLight class
    Has a gree, yellow and red light that need to be
    passed in
    """
    
    def __init__(self, green, yellow, red):
        """
        # Traffic light constructor
        # Add the green, yellow and red lights to the array
        # in that order.
        """
        
        print("TrafficLight constructor: add the lights in order")
        super().__init__()
        self._lights.append(green)
        self._lights.append(yellow)
        self._lights.append(red)
    
    def go(self):
        print("Trafficlight - go/green")
        self.singleOn(0)
    
    def caution(self):
        print("Trafficlight - caution/yellow")
        self.singleOn(1)

    def stop(self):
        print("Trafficlight - stop/red")
        self.singleOn(2)

    def run(self):
        """
        # The run method - just runs the cycle once, showing
        # Green, yellow then red, and going back to Green
        """
        
        super().run()
        print("TrafficLight: Run a simple Green-yellow-red sequence")
        if (self._running):
            self.go()
        if (self._running):
            sleep(3)
        if (self._running):
            self.caution()  
        if (self._running):
            sleep(0.5)
        if (self._running):
            self.stop()
        if (self._running):
            sleep(1.5)
        if (self._running):
            self.go()

class Pixel(CompositeLight):
    """
    The Pixel class - just uses an RGB LED to provide a simple implementation
    of a pixel that can be technically set to any color.
    """        

    def __init__(self, R, G, B, commoncathode = True):
        """     # Pixel constructor """

        print("Pixel: Constructor - add R G B in that order")
        super().__init__()
        self._lights.append(R)
        self._lights.append(G)
        self._lights.append(B)
        self._commoncathode = commoncathode
        self._running = False
        
    def on(self):
        print("Pixel: turning all components on")
        self._running = False
        if self._commoncathode:
            super().on()
        else:
            super().off()
            
    def off(self):
        print("Pixel: turning all components off")
        self._running = False
        if self._commoncathode:
            super().off()
        else:
            super().on()
       
    def setColor(self, RR, GG, BB):
        """
        # setColor method - sets to a specific color
        # Brightness is set as percentage in this app
        """
        
        print(f"Pixel: setColor: R:{RR}, G:{GG}, B:{BB}")
        self._lights[0].setBrightness(RR)
        self._lights[1].setBrightness(GG)
        self._lights[2].setBrightness(BB)
                
    def run(self, delay=250):
        """     # Demo run - just run up and down the R, G, B components """
        self._running = True

        colors = [[255,0,0], [255,165,0], [255,255,0], [0,128,0],[0,0,255],[75,0,130],[238,130,238]]
        print("Pixel - run - rainbow demo")
        for c in colors:
            if not self._running:
                break
            self.setColor(c[0],c[1],c[2])
            sleep_ms(delay)        
        self._running = False
         
class NeoPixel(CompositeLight):
    """
    Although technically a composite light, a neopixel is a PIO-driven set of lights
    using a single output pin. So you do not send it composite lights, but just the pin
    it is connected to. It is a composite light because it has multiple lights, but
    they cannot technically be controlled individually.
    """

    FILLS = 0
    CHASES = 1
    RAINBOW = 2

    def __init__(self, pin=22, numleds=16, brightness=0.5):
        """
        Constructor for neopixel will create its own internal statemachine
        Note that if any other state machine is running, this will break the existing
        statemachine. This refers to the Pico PIO statemachine, not any software state
        machines.
        """

        self._pin = pin
        self._numleds = numleds
        self._brightness = brightness
        self._running = False

        # Create the StateMachine with the ws2812 program, outputting on pin
        self._sm = rp2.StateMachine(0, ws2812, freq=8_000_000, sideset_base=Pin(self._pin))

        # Start the StateMachine, it will wait for data on its FIFO.
        self._sm.active(1)

        # Display a pattern on the LEDs via an array of LED RGB values.
        self._ar = array.array("I", [0 for _ in range(self._numleds)])

    def on(self):
        """ Turn all LEDs ON - all white """

        self.pixels_fill(WHITE)
        self.pixels_show()
    
    def off(self):
        """ Turn all LEDs OFF - all black """
        self._running = False
        sleep(0.1)
        self.pixels_fill(BLACK)
        self.pixels_show()

    def setColor(self, color, numPixels= -1):
        """
        Change the pixel colors to a specific color
        Color can be provided as a list (R,G,B) or pick one from the
        pre-defined colors below.
        
        Send a numPixels parameter to only light up a subset of the LEDs
        Sending a negative value will light up all lights
        """
        
        if numPixels < 0 or numPixels > len(self._ar):
            numPixels = len(self._ar)
        for i in range(numPixels):
            self.pixels_set(i, color)
        for i in range(numPixels,len(self._ar)):
            self.pixels_set(i, BLACK)
        self.pixels_show()

    def setBrightness(self, brightness=0.5):
        self._brightness = brightness

    def run(self, runtype=0):
        self._running = True
        if runtype == NeoPixel.FILLS:
            print("fills")
            for color in COLORS:
                if not self._running:
                    break       
                self.pixels_fill(color)
                self.pixels_show()
                sleep(0.2)
        elif runtype == NeoPixel.CHASES:
            print("chases")
            for color in COLORS:
                if not self._running:
                    break       
                self.color_chase(color, 0.01)
        else:
            print("rainbow")
            self.rainbow_cycle(0)
        self._running = False


    ################# Internal functions should not be used outside here #################
    def pixels_show(self):
        dimmer_ar = array.array("I", [0 for _ in range(self._numleds)])
        for i,c in enumerate(self._ar):
            r = int(((c >> 8) & 0xFF) * self._brightness)
            g = int(((c >> 16) & 0xFF) * self._brightness)
            b = int((c & 0xFF) * self._brightness)
            dimmer_ar[i] = (g<<16) + (r<<8) + b
        self._sm.put(dimmer_ar, 8)
        sleep_ms(10)

    def pixels_set(self, i, color):
        self._ar[i] = (color[1]<<16) + (color[0]<<8) + color[2]

    def pixels_fill(self, color):
        for i in range(len(self._ar)):
            self.pixels_set(i, color)

    def color_chase(self, color, wait):
        for i in range(self._numleds):
            if not self._running:
                break
            self.pixels_set(i, color)
            sleep(wait)
            self.pixels_show()
        sleep(0.2)
    
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
                self.pixels_set(i, self.wheel(rc_index & 255))
            self.pixels_show()
            sleep(wait)


# Internal definitions for the Pico PIO ASM
@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)    [T3 - 1]
    jmp(not_x, "do_zero")   .side(1)    [T1 - 1]
    jmp("bitloop")          .side(1)    [T2 - 1]
    label("do_zero")
    nop()                   .side(0)    [T2 - 1]
    wrap()

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


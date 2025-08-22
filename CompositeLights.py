"""
# CompositeLights.py
# A simple inheritance structure showing a fairly abstract CompositeLight
# class that has a set of lights, and two different implementations of it
# Author: Arijit Sengupta
"""

from time import sleep, sleep_ms
from machine import Pin
from Log import *
from Lights import *

class CompositeLight:
    """
    The base CompositeLight class - contains just an array
    and the on, off, run methods that subclasses should potentially override
    The base class simply calls on and off on all internal lights
    that may not be the proper way to turn on the composite
    """
    
    def __init__(self):
        """    # Constructor - just initialize the array of lights """

        Log.i("CompositeLight constructor")
        self._lights = []
        self._running = False
        
    def operate(self):
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
        
        Log.i("CompositeLight: turning on all lights")
        for l in self._lights:
            l.on()

    def off(self):
        """     # Turn off all the components """

        Log.i("CompositeLight: turning off all lights")
        for l in self._lights:
            l.off()
            
    def singleOn(self, lightno):
        """     # Turn a single light on (and the others off) """

        Log.i(f"CompositieLight - turning only light #{lightno} on")
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
    
    def __init__(self, rpin, ypin, gpin):
        """
        # Traffic light constructor
        # Add the green, yellow and red lights to the array
        # in that order.
        """
        
        Log.i("TrafficLight constructor: add the lights in order")
        super().__init__()
        self._lights.append(Light(rpin, 'red'))
        self._lights.append(Light(ypin, 'yellow'))
        self._lights.append(Light(gpin,'green'))
        self._running = False
        self.stop()
    
    def go(self):
        Log.i("Trafficlight - go/green")
        self.singleOn(2)
    
    def caution(self):
        Log.i("Trafficlight - caution/yellow")
        self.singleOn(1)

    def stop(self):
        Log.i("Trafficlight - stop/red")
        self.singleOn(0)

    def operate(self, gtime = 3, ytime = 0.5, rtime = 1.5):
        """
        # The operate method - just runs the cycle once, showing
        # Green, yellow then red
        """
        
        super().operate()
        Log.i("TrafficLight: Run a simple Green-yellow-red sequence")
        if (self._running):
            self.go()
        if (self._running):
            sleep(gtime)
        if (self._running):
            self.caution()  
        if (self._running):
            sleep(ytime)
        if (self._running):
            self.stop()
        if (self._running):
            sleep(rtime)

class Pixel(CompositeLight):
    """
    The Pixel class - just uses an RGB LED to provide a simple implementation
    of a pixel that can be technically set to any color.
    """        

    def __init__(self, Rpin, Gpin, Bpin, commoncathode = True):
        """     # Pixel constructor """

        Log.i("Pixel: Constructor - add R G B in that order")
        super().__init__()
        self._lights.append(DimLight(Rpin, 'PixelR'))
        self._lights.append(DimLight(Gpin, 'PixelG'))
        self._lights.append(DimLight(Bpin, 'PixelB'))
        self._commoncathode = commoncathode
        self._running = False
        
    def on(self):
        Log.i("Pixel: turning all components on")
        self._running = False
        if self._commoncathode:
            super().on()
        else:
            super().off()
            
    def off(self):
        Log.i("Pixel: turning all components off")
        self._running = False
        if self._commoncathode:
            super().off()
        else:
            super().on()
       
    def setColor(self, color):
        """
        # setColor method - sets to a specific color
        # color is an RGB tuple
        # Brightness is set as fraction in this app
        """
        
        Log.i(f"Pixel: setColor: {color}")
        if self._commoncathode:
            self._lights[0].setBrightness(color[0]/255)
            self._lights[1].setBrightness(color[1]/255)
            self._lights[2].setBrightness(color[2]/255)
        else:
            self._lights[0].setBrightness(1 - color[0]/255)
            self._lights[1].setBrightness(1 - color[1]/255)
            self._lights[2].setBrightness(1 - color[2]/255)            
                
    def operate(self, delay=250):
        """     # Demo run - just run up and down the R, G, B components """
        self._running = True

        colors = [(255,0,0), (255,165,0), (255,255,0), (0,128,0),(0,0,255),(75,0,130),(238,130,238)]
        Log.i("Pixel - run - rainbow demo")
        for c in colors:
            if not self._running:
                break
            self.setColor(c)
            sleep_ms(delay)        
        self._running = False


### The following code is for testing purposes only
if __name__ == "__main__":
    # Create a traffic light and run it
    traffic_light = TrafficLight(3, 4, 5)
    print(traffic_light)
    traffic_light.operate()

    # Create a pixel and run it
    pixel = Pixel(6, 7, 8, commoncathode=False)
    print(pixel)
    pixel.operate()
    
    # Turn off the lights
    traffic_light.off()
    pixel.off()
    Log.i("Testing complete - all lights turned off")

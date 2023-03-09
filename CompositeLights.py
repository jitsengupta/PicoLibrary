# A simple inheritance structure showing a fairly abstract CompositeLight
# class that has a set of lights, and two different implementations of it

from time import sleep

"""
The base CompositeLight class - contains just an array
and the on, off, run methods that subclasses should potentially override
The base class simply calls on and off on all internal lights
that may not be the proper way to turn on the composite
"""
class CompositeLight:
    
    # Constructor - just initialize the array of lights
    def __init__(self):
        print("CompositeLight constructor")
        self._lights = []
        self._running = False
        
    # Technically this is an abstract method but Python does not
    # correctly support it, so just an empty shell
    def run(self):
        self._running = True

    # Turn on all the componets. Note that in does not necessarily
    # get all items in order - but usually does
    def on(self):
        print("CompositeLight: turning on all lights")
        for l in self._lights:
            l.on()

    # Turn off all the components
    def off(self):
        print("CompositeLight: turning off all lights")
        for l in self._lights:
            l.off()
            
    # Turn a single light on (and the others off)
    def singleOn(self, lightno):
        print(f"CompositieLight - turning only light #{lightno} on")
        for i in range(0,len(self._lights)):
            if i == lightno:
                self._lights[i].on()
            else:
                self._lights[i].off()

    # The __str__ method - add this to any class to generate a 
    # Human readable version of the class
    def __str__(self)->str:
        return f"{type(self).__name__} with {len(self._lights)} lights"

        
"""
The first subclass of the CompositeLight class
Has a gree, yellow and red light that need to be
passed in
"""
class TrafficLight(CompositeLight):
    # Traffic light constructor
    # Add the green, yellow and red lights to the array
    # in that order.
    def __init__(self, green, yellow, red):
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

    # The run method - just runs the cycle once, showing
    # Green, yellow then red, and going back to Green
    def run(self):
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

"""
The Pixel class - just uses an RGB LED to provide a simple implementation
of a pixel that can be technically set to any color.
"""        
class Pixel(CompositeLight):
    # Pixel constructor
    def __init__(self, R, G, B, commoncathode = True):
        print("Pixel: Constructor - add R G B in that order")
        super().__init__()
        self._lights.append(R)
        self._lights.append(G)
        self._lights.append(B)
        self._commoncathode = commoncathode
        
    def on(self):
        print("Pixel: turning all components on")
        if self._commoncathode:
            super().on()
        else:
            super().off()
            
    def off(self):
        print("Pixel: turning all components off")
        if self._commoncathode:
            super().off()
        else:
            super().on()
       
    # setColor method - sets to a specific color
    # Brightness is set as percentage in this app
    def setColor(self, RR, GG, BB):
        print(f"Pixel: setColor: R:{RR}, G:{GG}, B:{BB}")
        self._lights[0].setBrightness(RR)
        self._lights[1].setBrightness(GG)
        self._lights[2].setBrightness(BB)
                
    # Demo run - just run up and down the R, G, B components
    def run(self):
        print("Pixel - run - updown all lights")
        for l in self._lights:
            l.upDown()        
         

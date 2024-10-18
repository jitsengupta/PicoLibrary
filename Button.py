"""
# Button.py - Object-Oriented implementation of a Button
# Also added a simple implementation of a single analog Joystick
# Author: Arijit Sengupta
"""

from machine import Pin, ADC
import time
from Log import *

class Button:
    """
    A simple Button class
    Create the button using Button(pinnumber, name, handler)
    handler is typically self, and create two methods buttonPressed and buttonReleased
    to handle the push and release of the button.
    The name of the button will be passed back to the handler to identify
    which button was pressed/released
    """
    
    def __init__(self, pin, name, *, handler=None, lowActive=True):
	"""
	Initialize attributes and other internal data
	"""
	
        self._pinNo = pin
        self._name = name
        Log.i(f'Button constructor: create button {name} at pin {pin}')
        if lowActive:
            self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self._pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self._debounce_time = 0
        self._lowActive = lowActive
        self._lastStatus = None
        self._handler = None
        self.setHandler(handler)
    
    def isPressed(self):
        """ Check if the button is pressed or not - useful if polling """
        
        return (self._lowActive and self._pin.value() ==0) or (not self._lowActive and self._pin.value() == 1)
    
    def setHandler(self, handler):
        """ 
	set the handler to a new handler. Pass None to remove existing handler
	"""
        
        # if the old handler was active already, or if the new handler is None, remove the irq
        if self._handler is not None or handler is None:
            self._pin.irq(handler = None)
    
        # Now set it to th enew handler
        self._handler = handler
        # Create the IRQ if the handler is not None
        if self._handler:
            self._pin.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler = self._callback)
        
    def _callback(self, pin):
        """ The private interrupt handler - will call appropriate handlers """
        
        t = time.ticks_ms()
        v = self._pin.value()
        if ((self._lastStatus == None or self._lastStatus != v) and t-self._debounce_time) > 50:
            self._debounce_time=t
            self._lastStatus = v
            if self._handler is not None:
                if self.isPressed():
                    self._handler.buttonPressed(self._name)
                else:
                    self._handler.buttonReleased(self._name)
        #self._debounce_time=t

class Joystick(Button):
    """
    A joystick is technically more than a Button, but this is an example
    of using a subclass to inherit some functionality, and adding other
    functions as needed. 

    So we implement a Joystick as a subclass of a button, with the internal
    button inherited from the Button class, and the horizontal and vertical
    axes implemented as ADC pin implementations. 

    Interestingly, we may have looked into AnalogSensor as well, but there is
    no tripping of a Joystick so we don't need that.
    """
    
    # Some constants to store some basic conditions
    LOW = 0
    HIGH = 65535
    MID = 32760

    # Joystick status codes
    CENTER = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    MOVING = 5
    
    # Status text
    statuscodes = ['Center', 'Up', 'Down', 'Left', 'Right', 'Moving']

    def __init__(self, vpin, hpin, swpin, name, *, handler=None, delta=1000):
        # Let the superclass handle all button functionality
        super().__init__(swpin, name, handler=handler, lowActive=True)
        Log.i(f'Joystick constructor: create joystick at v:{vpin}, h:{hpin}')

        # H and V axis pins must be standard ADC supporting
        if vpin <26 or vpin > 28 or hpin < 26 or hpin > 28:
            raise ValueError("Joystick Error: must connect v/h to ADC pins")

        self._v = ADC(vpin)
        self._h = ADC(hpin)
        self._delta = delta

    def getData(self):
        """
        A simple method to return the x and y values
        """

        return (self._h.read_u16(), self._v.read_u16())

    def getStatusCode(self):
        """
        Return the status code of the joystick
        0 - center, 1 left 2 right 3 up 4 down
        5 if it is not quite in any distinct position
        """

        (x,y) = self.getData()

        if x < self.LOW + self._delta:
            return self.RIGHT
        if x > self.HIGH - self._delta:
            return self.LEFT
        if y < self.LOW + self._delta:
            return self.DOWN
        if y > self.HIGH - self._delta:
            return self.UP
        if x > self.MID - self._delta and x < self.MID + self._delta and y > self.MID - self._delta and y < self.MID + self._delta:
            return self.CENTER
        return self.MOVING

    def getStatus(self):
        """
        Get the status of the joystick in text
        center, left, right, up, down, moving
        """
    
        return Joystick.statuscodes[self.getStatusCode()]

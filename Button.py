"""
# Button.py - Object-Oriented implementation of a Button
# Author: Arijit Sengupta
"""

from machine import Pin
import time

class Button:
    """
    A simple Button class
    Create the button using Button(pinnumber, name, handler)
    handler is typically self, and create two methods buttonPressed and buttonReleased
    to handle the push and release of the button.
    The name of the button will be passed back to the handler to identify
    which button was pressed/released
    """
    
    def __init__(self, pin, name, *, buttonhandler=None, lowActive=True):
        self._pinNo = pin
        self._name = name
        if lowActive:
            self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        else:
            self._pin = Pin(pin, Pin.IN, Pin.PULL_DOWN)
        self._debounce_time = 0
        self._lowActive = lowActive
        self._buttonhandler = buttonhandler
        self._pin.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler = self._callback)

    def isPressed(self):
        """ Check if the button is pressed or not - useful if polling """
        
        return (self._lowActive and self._pin.value() ==0) or (not self._lowActive and self._pin.value() == 1)
    
    def setHandler(self, buttonhandler):
        """ A class that has buttonPressed(name) and buttonReleased(name) methods """
        
        self._buttonhandler = buttonhandler
        
    def _callback(self, pin):
        """ The private interrupt handler - will call appropriate handlers """
        
        t = time.ticks_ms()
        if (t-self._debounce_time) > 100:
            self._debounce_time=t
            if self._buttonhandler is not None:
                if self.isPressed():
                    self._buttonhandler.buttonPressed(self._name)
                else:
                    self._buttonhandler.buttonReleased(self._name)
        self._debounce_time=t

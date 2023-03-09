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
    
    def __init__(self, pin, name, buttonhandler=None):
        self._pinNo = pin
        self._name = name
        self._pin = Pin(pin, Pin.IN, Pin.PULL_UP)
        self._debounce_time = 0
        self._buttonhandler = buttonhandler
        self._pin.irq(trigger = Pin.IRQ_FALLING | Pin.IRQ_RISING, handler = self._callback)

    def isPressed(self):
        """ Check if the button is pressed or not - useful if polling """
        
        return self._pin.value()
    
    def setHandler(buttonhandler):
        """ A class that has buttonPressed(name) and buttonReleased(name) methods """
        
        self._buttonhandler = buttonhandler
        
    def _callback(self, pin):
        """ The private interrupt handler - will call appropriate handlers """
        
        if (time.ticks_ms()-self._debounce_time) > 25:
            self._debounce_time=time.ticks_ms()
            if self._buttonhandler == None:
                return
            
            if (self._pin.value()):
                self._buttonhandler.buttonReleased(self._name)
            else:
                self._buttonhandler.buttonPressed(self._name)
    

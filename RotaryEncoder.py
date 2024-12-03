"""
# RotaryEncoder.py - Object-Oriented implementation of a Rotary Encoder
# Note that this only implements the encoder part of the hardware. If
# encoder has a built-in button use the Button class.
# This uses the popular micropython-rotary library by Mike Teachman
# See rotary_irq_rp2.py and rotary.py for additional information.
# Author: Arijit Sengupta
"""

from rotary_irq_rp2 import *

class RotaryEncoder:
    """
    A Rotary Encoder class. As per other PicoLibrary classes, this
    takes the two pins as ints, a name for the encoder and a handler object.

    The pin names are clk and dt, and the handler object must implement
    a callback method encoderUpdate(value, name)
    which will receive an update when the encoder Value changes.
    
    hander can be defaulted to None in which case you will need to poll
    the encoder and call the getValue() method to get the current value.

    Additional parameters:
    min = minimum value reported (default 0)
    max = maximum value reported (default 100)
    reverse = whether the direction of the encoder should be reversed
    range_mode = there are 3 options
    Rotary.RANGE_WRAP is default which will go to min once max is exceeded
       (and go to max when you go below min)
    Rotary.RANGE_BOUNDED will stay stuck at max if max is exceeded
    Rotary.RANGE_UNBOUNDED will ignore the min and max values and keep going up
    or down. 

    Sample code:
    def __init__(self):
        e = Rotary_Encoder(clk=13, dt=14, name='Encoder', hander=self)

    def encoderUpdate(self, value, name):
        print(f'Encoder {name} value changed to {value}')
    """

    def __init__(self, clk=13, dt=14, name='Rotary', handler = None, min=0, max=100, reverse=False, range_mode=Rotary.RANGE_WRAP):
        self._encoder = RotaryIRQ(pin_num_clk=clk,
                                    pin_num_dt=dt,
                                    min_val = min,
                                    max_val = max, 
                                    reverse = reverse,
                                    range_mode=range_mode)
        self._name = name
        self._handler = handler
        self._encoder.add_listener(self._listener)

    def getValue(self):
        """ Get the current value of the encoder """

        return self._encoder.value()

    def _listener(self):
        """ Internal - should not be called directly """

        if self._handler:
            v = self.getValue()
            self._handler.encoderUpdate(v, self._name)

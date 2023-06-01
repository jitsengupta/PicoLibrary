"""
# SevenSegSingle.py
# A simple implementation of a single seven segment display
# unit. Raw unit connected either directly through GPIO pins
# or using a shift register.
# To create the raw unit, send A=n, B=n, C=n... E=n as parameters
# To create the shift register version, send
# dataPin, clockPin and latchPin nos
#
# See a demo at: https://wokwi.com/projects/365454777517844481
# Author: Arijit Sengupta
"""


from machine import Pin
import random
import utime
import time

class SevenSegSingle:
    """
    SevenSegSingle class - implementation of a single seven-segment display
    Can be connected directly via GPIO or via a shift register

    Currently only displays numbers.
    
    Now supports both common-Cathode as well as common-Anode style displays
    
    Create a parallel common Cathode version:
    
    d = SevenSegSingle(A=0, B=1, C=2, D=3, E=4, F=5, G=6, commonCathode=True)
    
    Create a shift-registered common anode version:
    
    d = SevenSegSingle(dataPin=25, clockPin=26, latchPin=27, commonCathode=False)
    """

    def __init__(self, A=0, B=1, C=2, D=3, E=4, F=5, G=6,
                     commonCathode=True, *, dataPin=None, clockPin=None, latchPin=None):
        """
        Constructor - call as SevenSeg(A=n, B=n, C=n... G=n) for direct connection
        or as  SevenSeg(dataPin=n, clockPin=n, latchPin=n) if using a shift register
        """
  
        pinarray = [A, B, C, D, E, F, G]
        self._digitcodes = ["11111100", "01100000", "11011010", "11110010", "01100110",
                                "10110110", "10111110", "11100000", "11111110", "11110110"]
        self.commcathode = commonCathode
        self._parallelPins = []
        if dataPin is None:
            for p in range(0, 7):
                self._parallelPins.append(Pin(pinarray[p],Pin.OUT))
                self._data = None
        else:
            self._data = Pin(dataPin, Pin.OUT)
            self._latch = Pin(latchPin, Pin.OUT)
            self._clock = Pin(clockPin, Pin.OUT)

    def show(self, n):
        """
        Show a number on the seven segment display - only supports 0-9
        """

        if n < 0 or n > 9:
            raise ValueError('This class can only display a number between 0-9')
        else:
            if self._data is None:
                self._parallel_update(self._digitcodes[n])
            else:
                self._shift_update(self._digitcodes[n])

    def _valueOf(self, val)->int:
        if self.commcathode:
            return int(val)
        else:
            return 0 if int(val) == 1 else 1 

    def _parallel_update(self, input):
        for i in range(0,7):
            self._parallelPins[i].value(self._valueOf(input[i])) 

    def _shift_update(self, input):
        #put latch down to start data sending
        self._clock.value(0)
        self._latch.value(0)
        self._clock.value(1)

        #load data in reverse order
        for i in range(7, -1, -1):
            self._clock.value(0)
            self._data.value(self._valueOf(input[i]))
            self._clock.value(1)

        #put latch up to store data on register
        self._clock.value(0)
        self._latch.value(1)
        self._clock.value(1)

### Test this module if needed. Direct connect uses the default
### A=0 through G=7

if __name__ == '__main__':
    d1 = SevenSegSingle(dataPin = 16, clockPin = 18, latchPin = 17)
    d2 = SevenSegSingle()
    for i in range(0,100000):
        d1.show(i%10)
        d2.show(i%10)
        time.sleep(0.3)


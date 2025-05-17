"""
ExtADC.py - Implements an external ADC
and includes a Joystick implementation using
channels of an external ADC

Uses adc1x15.py driver from https://github.com/robert-hh/ads1x15
"""

from machine import I2C, Pin
from ads1x15 import *
from Button import *

class ExtADC:
    """
    Not creating this as a subclass of ADC since ADC has some
    abilities that I don't know much about. Eventually that might
    be a possible direction.
    
    Also, typically an external ACD has multiple channels of ADC.
    
    TODO: research possibilities of subclassing ADC for this
    """
    
    def __init__(self, sda, scl):
        i2cid = -1 # lets set an invalid value to start with
        if (sda == 0 and scl == 1) or (sda == 4 and scl == 5) or (sda == 8 and scl == 9) or (sda == 12 and scl == 13) or (sda == 16 and scl == 17) or (sda == 20 and scl == 21):    
            i2cid = 0
        elif (sda == 2 and scl == 3) or (sda == 6 and scl == 7) or (sda == 10 and scl == 11) or (sda == 14 and scl == 15) or (sda == 18 and scl == 19) or (sda == 26 and scl == 27):
            i2cid = 1
        else:
            raise ValueError('Invalid SDA/SCL pins')
        i2c = I2C(i2cid, sda=Pin(sda), scl=Pin(scl), freq=400000)
        self.adc = ADS1115(i2c, address=0x48, gain=1)

    def read_u16(self, channel):
        d = self.adc.read(4, channel)
        return d*2
    
    def read_uv(self, channel):
        d = self.adc.read(4, channel)
        voltage = adc.raw_to_v(value)
        return voltage * 1000
    
class ExtADCJoystick(Joystick):
    
    def __init__(self, adc, vchannel, hchannel, swpin, name, *, handler=None, delta=1000):
        super().__init__(vpin=None, hpin=None, swpin=swpin, name=name, handler=handler, delta=delta)
        self._adc = adc
        self._hchannel = hchannel
        self._vchannel = vchannel
        
    def getData(self):
        """
        A simple method to return the x and y values
        """

        return (self._adc.read_u16(self._hchannel), self._adc.read_u16(self._vchannel))

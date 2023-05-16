"""
# Sensors.py
# A simple Sensor hierarchy for digital and analog sensors
# Author: Arijit Sengupta
"""

from machine import Pin, ADC

class Sensor:
    """
    The top level sensor class - assume each sensor uses 
    at least one pin. We do not create the IO here because
    some sensors may use Analog inputs
    
    Parameters
    --------
    pin: pin number where the sensor is connected
    lowactive: set to True if the sensor gets low (or under threshold)
    when tripped. So an analog light sensor should normally get a high
    value but when covered, go low. So lowactive should be True
    
    A force sensor would be opposite - tripped when force gets high
    so lowactive should be False
    """
    
    def __init__(self, pin, lowactive = True):
        self._pin = pin
        self._lowactive = lowactive
        
    def tripped(self)->bool:
        print(f"tripped not implemented for {type(self).__name__}")
        return False

class DigitalSensor(Sensor):
    """
    A simple digital sensor (like the commonly available LC-393 that is a light sensor)
    has a digital output that flips based on a manual threshold control

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, lowactive=True):
        super().__init__(pin, lowactive)
        self._pinio = Pin(self._pin, Pin.IN)

    def tripped(self)->bool:
        v = self._pinio.value()
        if (self._lowactive and v == 0) or (not self._lowactive and v == 1):
            print("DigitalLightSensor: sensor tripped")
            return True
        else:
            return False

class AnalogSensor(Sensor):
    """
    A simple analog sensor that returns a voltage or voltage ratio output
    that can be read in using an ADC. Pico reads in via a 16bit unsigned

    We are just going to poll this to keep things simple
    """
    
    def __init__(self, pin, lowactive=True, threshold = 30000):
        """ analog sensors will need to be sent a threshold value to detect trip """
        
        super().__init__(pin, lowactive)
        self._pinio = ADC(self._pin)
        self._threshold = threshold

    def tripped(self)->bool:
        """ sensor is tripped if sensor value is higher or lower than threshold """
        
        v = self.rawValue()
        if (self._lowactive and v < self._threshold) or (not self._lowactive and v > self._threshold):
            print("AnalogLightSensor: sensor tripped")
            return True
        else:
            return False

    def rawValue(self):
        return self._pinio.read_u16()
